"""
ObraHunter - Scheduler de Tarefas Automáticas
Orquestrador central que roda buscas continuamente e dispara alertas
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import (
    BuscaAutomatica, ExecucaoBusca, Obra, Empresa,
    Decisor, ConfigAlerta, AlertaEnviado,
    StatusLead, FonteDados, FrequenciaBusca
)
from app.scrapers.google_maps import GoogleMapsScraper
from app.scrapers.diarios_oficiais import DiarioOficialScraper
from app.scrapers.licitacoes import LicitacoesScraper
from app.scrapers.construtoras import ConstrutorasScraper
from app.services.enriquecimento import EnriquecimentoService
from app.services.score import ScoreService
from app.services.alertas import AlertaService

logger = logging.getLogger(__name__)


class ObraHunterScheduler:
    """
    Scheduler principal do ObraHunter.
    Roda continuamente, executando buscas automáticas e processando resultados.
    """

    def __init__(self):
        self.score_service = ScoreService()
        self.alerta_service = AlertaService()
        self.running = False
        self.scrapers = {
            "google_maps": GoogleMapsScraper,
            "diario_oficial": DiarioOficialScraper,
            "licitacao": LicitacoesScraper,
            "construtora": ConstrutorasScraper,
        }

    async def iniciar(self):
        """Inicia o loop principal do scheduler"""
        self.running = True
        logger.info("🚀 ObraHunter Scheduler iniciado!")

        while self.running:
            try:
                await self._processar_buscas_pendentes()
                await asyncio.sleep(60)  # Verifica a cada 1 minuto
            except Exception as e:
                logger.error(f"Erro no scheduler: {e}")
                await asyncio.sleep(30)

    async def parar(self):
        """Para o scheduler"""
        self.running = False
        logger.info("⏹️ ObraHunter Scheduler parado")

    async def _processar_buscas_pendentes(self):
        """Verifica e executa buscas que estão no horário"""
        async with AsyncSessionLocal() as session:
            # Buscar automáticas ativas com próxima execução no passado
            result = await session.execute(
                select(BuscaAutomatica).where(
                    BuscaAutomatica.ativa == True,
                    (BuscaAutomatica.proxima_execucao <= datetime.utcnow()) |
                    (BuscaAutomatica.proxima_execucao == None)
                )
            )
            buscas = result.scalars().all()

            for busca in buscas:
                logger.info(f"▶️ Executando busca: {busca.nome} (ID: {busca.id})")
                await self.executar_busca(busca.id)

    async def executar_busca(self, busca_id: int) -> Dict:
        """
        Executa uma busca automática completa:
        1. Roda scrapers conforme filtros
        2. Salva obras novas no banco
        3. Enriquece dados
        4. Calcula scores
        5. Dispara alertas para boas oportunidades
        """
        async with AsyncSessionLocal() as session:
            # Carregar busca
            busca = await session.get(BuscaAutomatica, busca_id)
            if not busca:
                return {"error": "Busca não encontrada"}

            # Criar registro de execução
            execucao = ExecucaoBusca(
                busca_id=busca_id,
                status="running",
                inicio=datetime.utcnow(),
            )
            session.add(execucao)
            await session.flush()

            try:
                filtros = busca.filtros or {}

                # 1. RODAR SCRAPERS EM PARALELO
                resultados_scraper = await self._rodar_scrapers(filtros)

                # 2. SALVAR OBRAS NOVAS
                obras_novas = await self._salvar_obras(session, resultados_scraper)

                # 3. ENRIQUECER DADOS
                await self._enriquecer_obras(session, obras_novas)

                # 4. CALCULAR SCORES
                obras_com_score = await self._calcular_scores(session, obras_novas)

                # 5. DISPARAR ALERTAS
                alertas_enviados = await self._disparar_alertas(
                    session, busca, obras_com_score
                )

                # Atualizar execução
                execucao.status = "success"
                execucao.obras_encontradas = len(resultados_scraper)
                execucao.obras_novas = len(obras_novas)
                execucao.alertas_enviados = alertas_enviados
                execucao.fim = datetime.utcnow()
                execucao.duracao_segundos = (
                    execucao.fim - execucao.inicio
                ).total_seconds()

                # Atualizar busca
                busca.ultima_execucao = datetime.utcnow()
                busca.proxima_execucao = self._calcular_proxima_execucao(busca)
                busca.total_execucoes += 1
                busca.total_obras_encontradas += len(obras_novas)
                busca.total_alertas_enviados += alertas_enviados

                await session.commit()

                logger.info(
                    f"✅ Busca '{busca.nome}' concluída: "
                    f"{len(obras_novas)} novas obras, "
                    f"{alertas_enviados} alertas enviados"
                )

                return {
                    "status": "success",
                    "obras_novas": len(obras_novas),
                    "alertas_enviados": alertas_enviados,
                    "duracao": execucao.duracao_segundos,
                }

            except Exception as e:
                execucao.status = "error"
                execucao.erro = str(e)
                execucao.fim = datetime.utcnow()
                await session.commit()
                logger.error(f"❌ Erro na busca '{busca.nome}': {e}")
                return {"error": str(e)}

    async def _rodar_scrapers(self, filtros: Dict) -> List[Dict]:
        """Roda todos os scrapers em paralelo"""
        fontes = filtros.get("fontes", list(self.scrapers.keys()))
        tasks = []

        for fonte in fontes:
            scraper_class = self.scrapers.get(fonte)
            if scraper_class:
                scraper = scraper_class()
                tasks.append(scraper.executar(filtros))

        # Executar em paralelo com timeout
        resultados = []
        if tasks:
            done = await asyncio.gather(*tasks, return_exceptions=True)
            for resultado in done:
                if isinstance(resultado, Exception):
                    logger.error(f"Scraper error: {resultado}")
                elif isinstance(resultado, dict):
                    resultados.extend(resultado.get("results", []))

        return resultados

    async def _salvar_obras(
        self, session: AsyncSession, resultados: List[Dict]
    ) -> List[Obra]:
        """Salva obras novas no banco (evita duplicatas)"""
        obras_novas = []

        for dados in resultados:
            # Verificar duplicata
            fonte = dados.get("fonte", "")
            fonte_ref = dados.get("fonte_ref", "")

            if fonte_ref:
                existing = await session.execute(
                    select(Obra).where(
                        Obra.fonte == fonte,
                        Obra.fonte_ref == fonte_ref,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

            # Mapear tipo de obra
            tipo_map = {
                "residencial": "residencial",
                "comercial": "comercial",
                "industrial": "industrial",
                "infraestrutura": "infraestrutura",
                "loteamento": "loteamento",
                "reforma": "reforma",
                "institucional": "institucional",
                "misto": "misto",
            }

            obra = Obra(
                titulo=dados.get("titulo", "Sem título")[:500],
                endereco=dados.get("endereco"),
                cidade=dados.get("cidade"),
                estado=dados.get("estado"),
                bairro=dados.get("bairro"),
                cep=dados.get("cep"),
                latitude=dados.get("latitude"),
                longitude=dados.get("longitude"),
                tipo=tipo_map.get(dados.get("tipo_obra", ""), "residencial"),
                fase=dados.get("fase_obra", "desconhecida"),
                area_m2=dados.get("area_m2"),
                valor_estimado=dados.get("valor_estimado"),
                fonte=dados.get("fonte", "manual"),
                fonte_url=dados.get("fonte_url"),
                fonte_ref=dados.get("fonte_ref"),
                status=StatusLead.NOVO,
                dados_extras=dados.get("dados_extras"),
            )

            session.add(obra)
            obras_novas.append(obra)

            # Salvar empresa se disponível
            if dados.get("empresa_nome") or dados.get("empresa_cnpj"):
                empresa = await self._get_or_create_empresa(session, dados)
                if empresa:
                    obra.empresas.append(empresa)

        await session.flush()
        return obras_novas

    async def _get_or_create_empresa(
        self, session: AsyncSession, dados: Dict
    ) -> Optional[Empresa]:
        """Busca ou cria empresa no banco"""
        cnpj = dados.get("empresa_cnpj")
        nome = dados.get("empresa_nome")

        if cnpj:
            result = await session.execute(
                select(Empresa).where(Empresa.cnpj == cnpj)
            )
            empresa = result.scalar_one_or_none()
            if empresa:
                return empresa

        empresa = Empresa(
            cnpj=cnpj,
            nome_fantasia=nome,
            site=dados.get("empresa_site"),
        )
        session.add(empresa)
        await session.flush()
        return empresa

    async def _enriquecer_obras(
        self, session: AsyncSession, obras: List[Obra]
    ):
        """Enriquece dados das obras novas"""
        async with EnriquecimentoService() as enricher:
            for obra in obras[:10]:  # Limita a 10 por execução para não sobrecarregar
                try:
                    dados_obra = {
                        "empresa_cnpj": None,
                        "empresa_nome": None,
                        "empresa_site": None,
                    }

                    if obra.empresas:
                        emp = obra.empresas[0]
                        dados_obra["empresa_cnpj"] = emp.cnpj
                        dados_obra["empresa_nome"] = emp.nome_fantasia
                        dados_obra["empresa_site"] = emp.site

                    resultado = await enricher.enriquecer_obra(dados_obra)

                    # Atualizar empresa com dados do CNPJ
                    if resultado.get("empresa") and obra.empresas:
                        emp = obra.empresas[0]
                        dados_emp = resultado["empresa"]
                        emp.razao_social = dados_emp.get("razao_social") or emp.razao_social
                        emp.email = dados_emp.get("email") or emp.email
                        emp.telefone = dados_emp.get("telefone") or emp.telefone
                        emp.endereco_sede = dados_emp.get("endereco") or emp.endereco_sede
                        emp.cidade_sede = dados_emp.get("cidade") or emp.cidade_sede
                        emp.estado_sede = dados_emp.get("estado") or emp.estado_sede
                        emp.atividade_principal = dados_emp.get("atividade_principal")
                        emp.situacao_cadastral = dados_emp.get("situacao")
                        emp.socios = dados_emp.get("socios")

                    # Atualizar contatos do site
                    if resultado.get("contatos") and obra.empresas:
                        emp = obra.empresas[0]
                        contatos = resultado["contatos"]
                        if contatos.get("emails"):
                            emp.email = emp.email or contatos["emails"][0]
                        if contatos.get("whatsapp"):
                            emp.whatsapp = contatos["whatsapp"]
                        if contatos.get("instagram"):
                            emp.instagram = contatos["instagram"]
                        if contatos.get("linkedin"):
                            emp.linkedin = contatos["linkedin"]

                    # Salvar decisores sugeridos
                    for dec_data in resultado.get("decisores", []):
                        decisor = Decisor(
                            nome=dec_data["nome"],
                            cargo=dec_data.get("cargo"),
                            cargo_score=dec_data.get("cargo_score", 0),
                            linkedin_url=dec_data.get("linkedin_url"),
                            fonte_sugestao=dec_data.get("fonte"),
                            obra_id=obra.id,
                            empresa_id=obra.empresas[0].id if obra.empresas else None,
                        )
                        session.add(decisor)

                    obra.status = StatusLead.ENRIQUECIDO

                except Exception as e:
                    logger.warning(f"Erro enriquecendo obra {obra.id}: {e}")

        await session.flush()

    async def _calcular_scores(
        self, session: AsyncSession, obras: List[Obra]
    ) -> List[Obra]:
        """Calcula score de oportunidade para cada obra"""
        for obra in obras:
            dados = {
                "porte": obra.porte.value if obra.porte else "desconhecido",
                "fase": obra.fase.value if obra.fase else "desconhecida",
                "tipo": obra.tipo.value if obra.tipo else "desconhecido",
                "area_m2": obra.area_m2,
                "valor_estimado": obra.valor_estimado,
                "data_encontrada": obra.data_encontrada,
                "empresa_cnpj": bool(obra.empresas and obra.empresas[0].cnpj),
                "empresa_site": bool(obra.empresas and obra.empresas[0].site),
                "empresa_nome": bool(obra.empresas and obra.empresas[0].nome_fantasia),
                "tem_email": bool(obra.empresas and obra.empresas[0].email),
                "tem_telefone": bool(obra.empresas and obra.empresas[0].telefone),
            }
            obra.score_oportunidade = self.score_service.calcular_score(dados)

        await session.flush()
        return obras

    async def _disparar_alertas(
        self,
        session: AsyncSession,
        busca: BuscaAutomatica,
        obras: List[Obra],
    ) -> int:
        """Dispara alertas para obras com score acima do threshold"""
        total_enviados = 0

        # Carregar configurações de alerta
        result = await session.execute(
            select(ConfigAlerta).where(
                ConfigAlerta.busca_id == busca.id,
                ConfigAlerta.ativo == True,
            )
        )
        configs = result.scalars().all()

        if not configs:
            return 0

        for obra in obras:
            if obra.score_oportunidade < busca.score_minimo_alerta:
                continue

            if obra.alerta_enviado:
                continue

            motivo = self.score_service.gerar_motivo_alerta(
                {
                    "porte": obra.porte.value if obra.porte else "",
                    "fase": obra.fase.value if obra.fase else "",
                    "tipo": obra.tipo.value if obra.tipo else "",
                    "valor_estimado": obra.valor_estimado,
                    "area_m2": obra.area_m2,
                },
                obra.score_oportunidade,
            )

            obra_data = {
                "titulo": obra.titulo,
                "cidade": obra.cidade,
                "estado": obra.estado,
                "endereco": obra.endereco,
                "tipo": obra.tipo.value if obra.tipo else "",
                "fase": obra.fase.value if obra.fase else "",
                "empresa_nome": obra.empresas[0].nome_fantasia if obra.empresas else "N/A",
            }

            for config in configs:
                success = await self.alerta_service.enviar_alerta(
                    tipo=config.tipo.value,
                    destino=config.destino,
                    obra_data=obra_data,
                    score=obra.score_oportunidade,
                    motivo=motivo,
                )

                # Registrar alerta enviado
                alerta_reg = AlertaEnviado(
                    obra_id=obra.id,
                    tipo=config.tipo,
                    destino=config.destino,
                    conteudo=motivo,
                    sucesso=success,
                )
                session.add(alerta_reg)

                if success:
                    total_enviados += 1

            obra.alerta_enviado = True

        await session.flush()
        return total_enviados

    def _calcular_proxima_execucao(self, busca: BuscaAutomatica) -> datetime:
        """Calcula quando a próxima execução deve acontecer"""
        agora = datetime.utcnow()

        if busca.frequencia == FrequenciaBusca.CONTINUA:
            return agora + timedelta(minutes=settings.BUSCA_CONTINUA_INTERVALO_MIN)
        elif busca.frequencia == FrequenciaBusca.DIARIA:
            proxima = agora.replace(
                hour=settings.BUSCA_DIARIA_HORA, minute=0, second=0
            )
            if proxima <= agora:
                proxima += timedelta(days=1)
            return proxima
        elif busca.frequencia == FrequenciaBusca.SEMANAL:
            return agora + timedelta(weeks=1)
        elif busca.frequencia == FrequenciaBusca.PERSONALIZADA:
            intervalo = busca.intervalo_minutos or 60
            return agora + timedelta(minutes=intervalo)

        return agora + timedelta(hours=24)

    # ==================== EXECUÇÃO MANUAL ====================

    async def executar_busca_manual(self, filtros: Dict) -> Dict:
        """Executa uma busca única sem salvar como automática"""
        resultados = await self._rodar_scrapers(filtros)
        return {
            "total_encontrado": len(resultados),
            "resultados": resultados,
        }
