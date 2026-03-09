"""
ObraHunter - Serviço de Enriquecimento
Enriquece dados de obras com informações de empresas, contatos e decisores
"""
import re
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from bs4 import BeautifulSoup
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cargos-alvo para decisores (em ordem de prioridade)
CARGOS_ALVO = [
    {"cargo": "Diretor de Engenharia", "score": 10},
    {"cargo": "Diretor Técnico", "score": 10},
    {"cargo": "CEO", "score": 9},
    {"cargo": "Diretor Comercial", "score": 9},
    {"cargo": "Gerente de Obras", "score": 9},
    {"cargo": "Diretor de Operações", "score": 8},
    {"cargo": "Gerente de Engenharia", "score": 8},
    {"cargo": "Comprador", "score": 8},
    {"cargo": "Gerente de Suprimentos", "score": 8},
    {"cargo": "Gerente Comercial", "score": 7},
    {"cargo": "Engenheiro Responsável", "score": 7},
    {"cargo": "Coordenador de Obras", "score": 7},
    {"cargo": "Gerente de Projetos", "score": 6},
    {"cargo": "Engenheiro Civil", "score": 6},
    {"cargo": "Arquiteto", "score": 5},
    {"cargo": "Sócio", "score": 9},
    {"cargo": "Proprietário", "score": 10},
]


class EnriquecimentoService:
    """Serviço de enriquecimento de dados de obras e empresas"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Mozilla/5.0 (compatible; ObraHunter/1.0)"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    # ==================== CNPJ ====================

    async def consultar_cnpj(self, cnpj: str) -> Optional[Dict]:
        """
        Consulta dados de CNPJ via ReceitaWS (API gratuita)
        Retorna: razão social, nome fantasia, endereço, sócios, atividade
        """
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        if len(cnpj_limpo) != 14:
            logger.warning(f"CNPJ inválido: {cnpj}")
            return None

        urls = [
            f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}",
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}",
            f"https://publica.cnpj.ws/cnpj/{cnpj_limpo}",
        ]

        for url in urls:
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_cnpj_response(data, url)
                    elif resp.status == 429:
                        logger.info(f"Rate limit em {url}, tentando próxima...")
                        continue
            except Exception as e:
                logger.debug(f"Erro consultando {url}: {e}")
                continue

        return None

    def _parse_cnpj_response(self, data: Dict, source_url: str) -> Dict:
        """Normaliza resposta de diferentes APIs de CNPJ"""
        if "receitaws" in source_url:
            socios = []
            for socio in data.get("qsa", []):
                socios.append({
                    "nome": socio.get("nome"),
                    "qualificacao": socio.get("qual"),
                })

            return {
                "cnpj": data.get("cnpj"),
                "razao_social": data.get("nome"),
                "nome_fantasia": data.get("fantasia"),
                "email": data.get("email"),
                "telefone": data.get("telefone"),
                "endereco": f"{data.get('logradouro', '')}, {data.get('numero', '')} - {data.get('bairro', '')}",
                "cidade": data.get("municipio"),
                "estado": data.get("uf"),
                "cep": data.get("cep"),
                "atividade_principal": data.get("atividade_principal", [{}])[0].get("text", ""),
                "situacao": data.get("situacao"),
                "porte": data.get("porte"),
                "socios": socios,
            }
        elif "brasilapi" in source_url:
            socios = []
            for socio in data.get("qsa", []):
                socios.append({
                    "nome": socio.get("nome_socio"),
                    "qualificacao": socio.get("qualificacao_socio"),
                })

            return {
                "cnpj": data.get("cnpj"),
                "razao_social": data.get("razao_social"),
                "nome_fantasia": data.get("nome_fantasia"),
                "email": data.get("email"),
                "telefone": data.get("ddd_telefone_1"),
                "endereco": f"{data.get('logradouro', '')}, {data.get('numero', '')} - {data.get('bairro', '')}",
                "cidade": data.get("municipio"),
                "estado": data.get("uf"),
                "atividade_principal": data.get("cnae_fiscal_descricao"),
                "situacao": data.get("descricao_situacao_cadastral"),
                "porte": data.get("porte"),
                "socios": socios,
            }

        return data

    # ==================== CONTATOS DO SITE ====================

    async def extrair_contatos_site(self, url: str) -> Dict:
        """
        Faz scraping do site da empresa para extrair emails, telefones, WhatsApp
        """
        contatos = {
            "emails": [],
            "telefones": [],
            "whatsapp": None,
            "instagram": None,
            "facebook": None,
            "linkedin": None,
        }

        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return contatos
                html = await resp.text()
        except Exception as e:
            logger.debug(f"Erro acessando {url}: {e}")
            return contatos

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()

        # Extrair emails
        emails = re.findall(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            text
        )
        contatos["emails"] = list(set(
            e for e in emails
            if not any(x in e for x in ["example", "teste", "sentry", "webpack"])
        ))

        # Extrair telefones
        telefones = re.findall(
            r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-.\s]?\d{4}',
            text
        )
        contatos["telefones"] = list(set(telefones[:5]))

        # Extrair WhatsApp (links wa.me)
        whatsapp_links = soup.find_all("a", href=re.compile(r'wa\.me|whatsapp|api\.whatsapp'))
        if whatsapp_links:
            href = whatsapp_links[0].get("href", "")
            match = re.search(r'(\d{10,13})', href)
            if match:
                contatos["whatsapp"] = match.group(1)

        # Extrair redes sociais
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "instagram.com" in href:
                contatos["instagram"] = href
            elif "facebook.com" in href:
                contatos["facebook"] = href
            elif "linkedin.com" in href:
                contatos["linkedin"] = href

        # Tentar achar página de contato
        contact_links = soup.find_all("a", href=re.compile(r'contato|contact|fale'))
        if contact_links:
            contact_url = contact_links[0].get("href", "")
            if not contact_url.startswith("http"):
                contact_url = url.rstrip("/") + "/" + contact_url.lstrip("/")
            # Scrape a página de contato também
            try:
                async with self.session.get(contact_url) as resp:
                    if resp.status == 200:
                        contact_html = await resp.text()
                        contact_soup = BeautifulSoup(contact_html, "html.parser")
                        contact_text = contact_soup.get_text()

                        more_emails = re.findall(
                            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                            contact_text
                        )
                        contatos["emails"].extend(more_emails)
                        contatos["emails"] = list(set(contatos["emails"]))
            except Exception:
                pass

        return contatos

    # ==================== DECISORES (BUSCA ASSISTIDA) ====================

    async def sugerir_decisores(
        self,
        empresa_nome: str,
        socios: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Sugere decisores para uma empresa.
        Cruza: sócios da Receita + busca Google por perfis LinkedIn.
        NÃO faz scraping do LinkedIn - apenas busca Google.
        """
        sugestoes = []

        # 1. Sócios da Receita Federal como decisores
        if socios:
            for socio in socios:
                nome = socio.get("nome", "")
                qualificacao = socio.get("qualificacao", "")
                if nome:
                    cargo_info = self._mapear_cargo_socio(qualificacao)
                    sugestoes.append({
                        "nome": nome,
                        "cargo": cargo_info["cargo"],
                        "cargo_score": cargo_info["score"],
                        "linkedin_url": None,
                        "fonte": "receita_federal",
                    })

        # 2. Busca Google por perfis LinkedIn
        google_sugestoes = await self._buscar_decisores_google(empresa_nome)
        sugestoes.extend(google_sugestoes)

        # 3. Rankear e deduplicar
        sugestoes = self._rankear_decisores(sugestoes)

        return sugestoes[:10]  # Top 10 sugestões

    async def _buscar_decisores_google(self, empresa_nome: str) -> List[Dict]:
        """
        Busca no Google por perfis LinkedIn relacionados à empresa.
        Usa snippets do Google, NÃO acessa LinkedIn diretamente.
        """
        sugestoes = []

        for cargo_info in CARGOS_ALVO[:5]:  # Top 5 cargos
            query = f'"{empresa_nome}" "{cargo_info["cargo"]}" site:linkedin.com/in/'

            try:
                async with self.session.get(
                    "https://www.google.com/search",
                    params={"q": query, "num": 5}
                ) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text()
            except Exception:
                continue

            soup = BeautifulSoup(html, "html.parser")

            for g in soup.find_all("div", class_="g"):
                try:
                    title = g.find("h3")
                    link = g.find("a")
                    snippet = g.find("span", class_="aCOpRe") or g.find("div", class_="VwiC3b")

                    if not title or not link:
                        continue

                    title_text = title.get_text()
                    link_url = link.get("href", "")
                    snippet_text = snippet.get_text() if snippet else ""

                    # Verificar se é perfil LinkedIn
                    if "linkedin.com/in/" not in link_url:
                        continue

                    # Extrair nome do título (formato: "Nome Sobrenome - Cargo - Empresa")
                    nome = title_text.split(" - ")[0].strip() if " - " in title_text else title_text
                    nome = re.sub(r'\s*\|.*$', '', nome)  # Remove "| LinkedIn"

                    # Detectar cargo no snippet/título
                    cargo_detectado = self._detectar_cargo_texto(
                        f"{title_text} {snippet_text}"
                    )

                    if nome and len(nome) > 3:
                        sugestoes.append({
                            "nome": nome,
                            "cargo": cargo_detectado or cargo_info["cargo"],
                            "cargo_score": cargo_info["score"],
                            "linkedin_url": link_url,
                            "fonte": "google_linkedin",
                        })
                except Exception:
                    continue

        return sugestoes

    def _mapear_cargo_socio(self, qualificacao: str) -> Dict:
        """Mapeia qualificação da Receita para cargo e score"""
        q = qualificacao.lower() if qualificacao else ""

        if "administrador" in q or "diretor" in q:
            return {"cargo": "Diretor/Administrador", "score": 9}
        if "sócio" in q:
            return {"cargo": "Sócio", "score": 8}
        if "presidente" in q:
            return {"cargo": "Presidente", "score": 10}
        if "gerente" in q:
            return {"cargo": "Gerente", "score": 7}
        return {"cargo": qualificacao or "Sócio", "score": 6}

    def _detectar_cargo_texto(self, texto: str) -> Optional[str]:
        """Detecta cargo mais relevante em um texto"""
        texto_lower = texto.lower()
        for cargo_info in CARGOS_ALVO:
            if cargo_info["cargo"].lower() in texto_lower:
                return cargo_info["cargo"]
        return None

    def _rankear_decisores(self, sugestoes: List[Dict]) -> List[Dict]:
        """Remove duplicatas e ordena por score"""
        # Deduplicar por nome
        seen_names = set()
        unique = []
        for s in sugestoes:
            nome_key = s["nome"].lower().strip()
            if nome_key not in seen_names:
                seen_names.add(nome_key)
                unique.append(s)

        # Ordenar por cargo_score (maior primeiro)
        unique.sort(key=lambda x: x.get("cargo_score", 0), reverse=True)
        return unique

    # ==================== ENRIQUECIMENTO COMPLETO ====================

    async def enriquecer_obra(self, obra_data: Dict) -> Dict:
        """
        Pipeline completo de enriquecimento de uma obra.
        1. Consultar CNPJ (se disponível)
        2. Extrair contatos do site
        3. Sugerir decisores
        """
        resultado = {
            "empresa": None,
            "contatos": None,
            "decisores": [],
        }

        cnpj = obra_data.get("empresa_cnpj")
        empresa_nome = obra_data.get("empresa_nome")
        empresa_site = obra_data.get("empresa_site")

        # 1. CNPJ
        if cnpj:
            dados_cnpj = await self.consultar_cnpj(cnpj)
            if dados_cnpj:
                resultado["empresa"] = dados_cnpj
                if not empresa_nome:
                    empresa_nome = dados_cnpj.get("nome_fantasia") or dados_cnpj.get("razao_social")

        # 2. Contatos do site
        if empresa_site:
            contatos = await self.extrair_contatos_site(empresa_site)
            resultado["contatos"] = contatos

        # 3. Decisores
        if empresa_nome:
            socios = resultado.get("empresa", {}).get("socios") if resultado["empresa"] else None
            decisores = await self.sugerir_decisores(empresa_nome, socios)
            resultado["decisores"] = decisores

        return resultado
