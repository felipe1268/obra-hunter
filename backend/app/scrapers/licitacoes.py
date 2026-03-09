"""
ObraHunter - Scraper Licitações
Busca licitações de obras públicas em portais oficiais
"""
import re
import logging
from typing import List, Dict, Any, Optional
from app.scrapers.base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)

# Portais de licitação
PORTAIS_LICITACAO = [
    {
        "nome": "ComprasNet (Gov Federal)",
        "url": "https://www.gov.br/compras/pt-br",
        "api_url": "https://compras.dados.gov.br/licitacoes/v1/licitacoes.json",
    },
    {
        "nome": "BLL - Bolsa de Licitações",
        "url": "https://bll.org.br",
        "busca_url": "https://bll.org.br/busca",
    },
    {
        "nome": "Portal Nacional de Contratações Públicas (PNCP)",
        "url": "https://pncp.gov.br",
        "api_url": "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
    },
    {
        "nome": "Licitações-e (Banco do Brasil)",
        "url": "https://www.licitacoes-e.com.br",
    },
    {
        "nome": "TCE Transparência",
        "url": "https://painel.tce.sp.gov.br",
    },
]

# Palavras-chave para licitações de obra
KEYWORDS_OBRA = [
    "construção",
    "obra civil",
    "edificação",
    "reforma predial",
    "pavimentação",
    "terraplanagem",
    "saneamento",
    "drenagem",
    "ponte",
    "viaduto",
    "escola construção",
    "hospital construção",
    "praça construção",
    "quadra esportiva",
]

# Modalidades de licitação
MODALIDADES = [
    "concorrência",
    "tomada de preços",
    "convite",
    "pregão",
    "RDC",
    "concurso",
]


class LicitacoesScraper(BaseScraper):
    """
    Scraper para portais de licitações.
    Busca editais de obras públicas em múltiplos portais.
    """

    def get_fonte(self) -> str:
        return "licitacao"

    async def buscar(self, filtros: Dict[str, Any]) -> List[ScraperResult]:
        results = []

        # Buscar no ComprasNet / PNCP (API oficial)
        results.extend(await self._buscar_comprasnet(filtros))

        # Buscar no PNCP
        results.extend(await self._buscar_pncp(filtros))

        # Busca agregada via Google
        results.extend(await self._busca_google_licitacoes(filtros))

        return self._deduplicar(results)

    async def _buscar_comprasnet(self, filtros: Dict) -> List[ScraperResult]:
        """Busca via API do ComprasNet / Dados Abertos"""
        results = []
        url = "https://compras.dados.gov.br/licitacoes/v1/licitacoes.json"

        for keyword in KEYWORDS_OBRA[:5]:
            params = {
                "objeto": keyword,
                "offset": 0,
                "limit": 50,
            }

            # Filtrar por UF se especificado
            estados = filtros.get("estados", [])
            if estados:
                for estado in estados:
                    params["uf"] = estado
                    data = await self.fetch_json(url, params)
                    if data and "_embedded" in data:
                        for item in data["_embedded"].get("licitacoes", []):
                            result = self._parse_comprasnet(item)
                            if result:
                                results.append(result)
            else:
                data = await self.fetch_json(url, params)
                if data and "_embedded" in data:
                    for item in data["_embedded"].get("licitacoes", []):
                        result = self._parse_comprasnet(item)
                        if result:
                            results.append(result)

        return results

    def _parse_comprasnet(self, item: Dict) -> Optional[ScraperResult]:
        """Parse resultado da API ComprasNet"""
        objeto = item.get("objeto", "")

        # Verificar se é obra civil
        if not self._is_obra(objeto):
            return None

        valor = None
        if item.get("valor"):
            try:
                valor = float(item["valor"])
            except (ValueError, TypeError):
                pass

        return ScraperResult(
            titulo=objeto[:500],
            fonte="licitacao",
            fonte_url=item.get("link_edital"),
            fonte_ref=item.get("numero_licitacao"),
            cidade=item.get("municipio"),
            estado=item.get("uf"),
            tipo_obra=self._detectar_tipo_obra(objeto),
            valor_estimado=valor,
            empresa_nome=item.get("orgao"),
            data_publicacao=item.get("data_publicacao"),
            dados_extras={
                "modalidade": item.get("modalidade"),
                "situacao": item.get("situacao"),
                "orgao": item.get("orgao"),
                "uasg": item.get("uasg"),
                "numero_aviso": item.get("numero_aviso"),
            },
        )

    async def _buscar_pncp(self, filtros: Dict) -> List[ScraperResult]:
        """Busca via Portal Nacional de Contratações Públicas"""
        results = []
        url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

        params = {
            "dataInicial": filtros.get("data_inicio", ""),
            "dataFinal": filtros.get("data_fim", ""),
            "codigoModalidadeContratacao": "",
            "pagina": 1,
            "tamanhoPagina": 50,
        }

        # Buscar por palavras-chave de obra
        for keyword in KEYWORDS_OBRA[:3]:
            params["q"] = keyword
            data = await self.fetch_json(url, params)
            if data and isinstance(data, list):
                for item in data:
                    result = self._parse_pncp(item)
                    if result:
                        results.append(result)

        return results

    def _parse_pncp(self, item: Dict) -> Optional[ScraperResult]:
        """Parse resultado do PNCP"""
        objeto = item.get("objetoCompra", "")
        if not self._is_obra(objeto):
            return None

        return ScraperResult(
            titulo=objeto[:500],
            fonte="licitacao",
            fonte_url=item.get("linkSistemaOrigem"),
            fonte_ref=item.get("numeroControlePNCP"),
            cidade=item.get("municipio", {}).get("nomeIBGE") if isinstance(item.get("municipio"), dict) else None,
            estado=item.get("unidadeOrgao", {}).get("ufSigla") if isinstance(item.get("unidadeOrgao"), dict) else None,
            tipo_obra=self._detectar_tipo_obra(objeto),
            valor_estimado=item.get("valorTotalEstimado"),
            empresa_nome=item.get("orgaoEntidade", {}).get("razaoSocial") if isinstance(item.get("orgaoEntidade"), dict) else None,
            dados_extras={
                "modalidade": item.get("modalidadeNome"),
                "situacao": item.get("situacaoCompraNome"),
                "srp": item.get("srp"),
            },
        )

    async def _busca_google_licitacoes(self, filtros: Dict) -> List[ScraperResult]:
        """Fallback: busca Google por licitações de obras"""
        results = []
        estados = filtros.get("estados", ["SP", "RJ", "MG"])

        for keyword in KEYWORDS_OBRA[:2]:
            for estado in estados[:3]:
                query = f'licitação "{keyword}" {estado} edital 2024 2025'
                # Busca via Google (mesmo padrão do diários oficiais)
                html = await self.fetch(
                    "https://www.google.com/search",
                    params={"q": query, "num": 10, "lr": "lang_pt"}
                )
                if html:
                    parsed = self._parse_google_results(html)
                    results.extend(parsed)

        return results

    def _parse_google_results(self, html: str) -> List[ScraperResult]:
        """Parse resultados de busca do Google"""
        results = []
        soup = self.parse_html(html)

        for g in soup.find_all("div", class_="g"):
            title_tag = g.find("h3")
            link_tag = g.find("a")
            snippet_tag = g.find("span", class_="aCOpRe")

            if title_tag and link_tag:
                title = title_tag.get_text()
                link = link_tag.get("href", "")
                snippet = snippet_tag.get_text() if snippet_tag else ""
                full_text = f"{title} {snippet}"

                if self._is_obra(full_text):
                    results.append(ScraperResult(
                        titulo=title,
                        fonte="licitacao",
                        fonte_url=link,
                        tipo_obra=self._detectar_tipo_obra(full_text),
                        dados_extras={"snippet": snippet},
                    ))

        return results

    def _is_obra(self, texto: str) -> bool:
        """Verifica se o texto se refere a uma obra civil"""
        texto_lower = texto.lower()
        keywords = [
            "construção", "obra", "edificação", "reforma",
            "pavimentação", "terraplanagem", "drenagem",
            "saneamento", "ponte", "viaduto", "escola",
        ]
        return any(kw in texto_lower for kw in keywords)

    def _detectar_tipo_obra(self, texto: str) -> str:
        """Detecta tipo de obra a partir do texto"""
        texto_lower = texto.lower()
        if any(w in texto_lower for w in ["escola", "hospital", "UBS", "creche", "posto"]):
            return "institucional"
        if any(w in texto_lower for w in ["residencial", "habitacional", "moradia"]):
            return "residencial"
        if any(w in texto_lower for w in ["pavimentação", "ponte", "viaduto", "estrada"]):
            return "infraestrutura"
        if any(w in texto_lower for w in ["comercial", "mercado", "galpão"]):
            return "comercial"
        return "infraestrutura"  # Default para licitações

    def _deduplicar(self, results: List[ScraperResult]) -> List[ScraperResult]:
        seen = set()
        unique = []
        for r in results:
            key = r.fonte_ref or r.titulo[:80]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
