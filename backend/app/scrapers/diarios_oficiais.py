"""
ObraHunter - Scraper Diários Oficiais
Busca alvarás de construção e licenças em diários oficiais municipais/estaduais
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.scrapers.base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)

# Fontes de diários oficiais por estado
FONTES_DIARIOS = {
    "SP": [
        {
            "nome": "Diário Oficial SP",
            "url": "https://www.imprensaoficial.com.br",
            "busca_url": "https://www.imprensaoficial.com.br/DO/BuscaDO2001Resultado_11_3.aspx",
        },
    ],
    "RJ": [
        {
            "nome": "Diário Oficial RJ",
            "url": "https://www.ioerj.com.br",
        },
    ],
    "MG": [
        {
            "nome": "Diário Oficial MG",
            "url": "https://www.jornalminasgerais.mg.gov.br",
        },
    ],
    # Portais agregadores nacionais
    "_nacional": [
        {
            "nome": "Diário Oficial da União",
            "url": "https://www.in.gov.br/servicos/diario-oficial-da-uniao",
            "busca_url": "https://www.in.gov.br/consulta",
        },
        {
            "nome": "QD Online - Diários Municipais",
            "url": "https://www.diariomunicipal.com.br",
        },
        {
            "nome": "Diário Oficial dos Municípios",
            "url": "https://www.diariomunicipal.org",
        },
    ],
}

# Palavras-chave para identificar publicações de obras
KEYWORDS_ALVARA = [
    "alvará de construção",
    "alvará de obra",
    "licença de construção",
    "licença para construir",
    "licença de obra",
    "habite-se",
    "auto de conclusão",
    "aprovação de projeto",
    "certidão de conclusão",
    "embargo de obra",
    "liberação de obra",
]

KEYWORDS_LICITACAO_DO = [
    "licitação construção",
    "edital construção",
    "concorrência obra",
    "tomada de preço obra",
    "convite obra civil",
]


class DiarioOficialScraper(BaseScraper):
    """
    Scraper para diários oficiais.
    Busca publicações de alvarás, licenças e licitações de construção.
    """

    def get_fonte(self) -> str:
        return "diario_oficial"

    async def buscar(self, filtros: Dict[str, Any]) -> List[ScraperResult]:
        results = []
        estados = filtros.get("estados", list(FONTES_DIARIOS.keys()))
        periodo_dias = filtros.get("periodo_dias", 7)

        # Buscar em portais nacionais
        for fonte in FONTES_DIARIOS.get("_nacional", []):
            new_results = await self._buscar_portal(fonte, filtros, periodo_dias)
            results.extend(new_results)

        # Buscar em portais estaduais
        for estado in estados:
            if estado in FONTES_DIARIOS:
                for fonte in FONTES_DIARIOS[estado]:
                    new_results = await self._buscar_portal(fonte, filtros, periodo_dias)
                    results.extend(new_results)

        # Busca via Google (fallback inteligente)
        results.extend(await self._busca_google_diarios(filtros, periodo_dias))

        return self._deduplicar(results)

    async def _buscar_portal(
        self, fonte: Dict, filtros: Dict, periodo_dias: int
    ) -> List[ScraperResult]:
        """Busca em um portal específico de diário oficial"""
        results = []
        url = fonte.get("busca_url", fonte["url"])

        for keyword in KEYWORDS_ALVARA[:3]:  # Top 3 keywords
            html = await self.fetch(url, params={"q": keyword})
            if html:
                parsed = await self._parse_resultados_diario(html, fonte["nome"])
                results.extend(parsed)

        return results

    async def _busca_google_diarios(
        self, filtros: Dict, periodo_dias: int
    ) -> List[ScraperResult]:
        """
        Usa busca Google como fallback para encontrar publicações
        em diários oficiais de qualquer município
        """
        results = []
        estados = filtros.get("estados", ["SP", "RJ", "MG", "PR", "SC", "RS", "BA"])
        cidades = filtros.get("cidades", [])

        for keyword in KEYWORDS_ALVARA[:2]:
            for estado in estados[:5]:
                if cidades:
                    for cidade in cidades:
                        query = f'"{keyword}" "{cidade}" "{estado}" diário oficial'
                        search_results = await self._google_search(query, periodo_dias)
                        results.extend(search_results)
                else:
                    query = f'"{keyword}" "{estado}" diário oficial'
                    search_results = await self._google_search(query, periodo_dias)
                    results.extend(search_results)

        return results

    async def _google_search(
        self, query: str, periodo_dias: int
    ) -> List[ScraperResult]:
        """Busca no Google por publicações de diários oficiais"""
        results = []

        # Google Custom Search API ou scraping
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "dateRestrict": f"d{periodo_dias}",
            "num": 10,
            "lr": "lang_pt",
        }

        # Se não tiver API key, usar fallback
        data = await self.fetch_json(url, params)
        if data and "items" in data:
            for item in data["items"]:
                result = self._parse_google_result(item)
                if result:
                    results.append(result)

        return results

    def _parse_google_result(self, item: Dict) -> Optional[ScraperResult]:
        """Parse resultado do Google Search"""
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        # Extrair dados da publicação
        dados = self._extrair_dados_publicacao(title + " " + snippet)
        if not dados:
            return None

        return ScraperResult(
            titulo=dados.get("titulo", title),
            fonte="diario_oficial",
            fonte_url=link,
            fonte_ref=dados.get("numero_alvara"),
            endereco=dados.get("endereco"),
            cidade=dados.get("cidade"),
            estado=dados.get("estado"),
            tipo_obra=dados.get("tipo_obra", "desconhecido"),
            empresa_nome=dados.get("empresa"),
            empresa_cnpj=dados.get("cnpj"),
            data_publicacao=dados.get("data_publicacao"),
            dados_extras={
                "snippet": snippet,
                "tipo_publicacao": dados.get("tipo_publicacao"),
            },
        )

    async def _parse_resultados_diario(
        self, html: str, fonte_nome: str
    ) -> List[ScraperResult]:
        """Parse HTML de resultados de busca em diários oficiais"""
        results = []
        soup = self.parse_html(html)

        # Procurar por blocos de resultado (genérico)
        for article in soup.find_all(["article", "div", "li"], class_=re.compile(r"result|item|materia")):
            text = article.get_text(strip=True)
            dados = self._extrair_dados_publicacao(text)

            if dados:
                link_tag = article.find("a")
                link = link_tag["href"] if link_tag else None

                results.append(ScraperResult(
                    titulo=dados.get("titulo", text[:200]),
                    fonte="diario_oficial",
                    fonte_url=link,
                    fonte_ref=dados.get("numero_alvara"),
                    endereco=dados.get("endereco"),
                    cidade=dados.get("cidade"),
                    estado=dados.get("estado"),
                    tipo_obra=dados.get("tipo_obra"),
                    empresa_nome=dados.get("empresa"),
                    empresa_cnpj=dados.get("cnpj"),
                    dados_extras={"portal": fonte_nome},
                ))

        return results

    def _extrair_dados_publicacao(self, texto: str) -> Optional[Dict]:
        """
        Extrai dados estruturados de texto de publicação oficial
        usando regex patterns para alvarás e licenças
        """
        if not any(kw in texto.lower() for kw in
                    ["alvará", "licença", "construção", "obra", "habite-se"]):
            return None

        dados = {}

        # Extrair nº do alvará
        alvara_match = re.search(
            r'(?:alvará|licença|auto)[:\s]*(?:n[°ºo\.]*\s*)?(\d[\d\./-]+)',
            texto, re.IGNORECASE
        )
        if alvara_match:
            dados["numero_alvara"] = alvara_match.group(1)

        # Extrair endereço
        end_match = re.search(
            r'(?:rua|av\.?|avenida|alameda|travessa|praça|estrada|rodovia)\s+[^,\n]{5,80}',
            texto, re.IGNORECASE
        )
        if end_match:
            dados["endereco"] = end_match.group(0).strip()

        # Extrair CNPJ
        cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
        if cnpj_match:
            dados["cnpj"] = cnpj_match.group(0)

        # Extrair área
        area_match = re.search(r'([\d.,]+)\s*m[²2]', texto)
        if area_match:
            area_str = area_match.group(1).replace(".", "").replace(",", ".")
            try:
                dados["area_m2"] = float(area_str)
            except ValueError:
                pass

        # Detectar tipo de publicação
        if "habite-se" in texto.lower() or "conclusão" in texto.lower():
            dados["tipo_publicacao"] = "habite-se"
        elif "alvará" in texto.lower():
            dados["tipo_publicacao"] = "alvara"
        elif "licença" in texto.lower():
            dados["tipo_publicacao"] = "licenca"
        else:
            dados["tipo_publicacao"] = "outro"

        # Detectar tipo de obra
        if any(w in texto.lower() for w in ["residencial", "apartamento", "casa"]):
            dados["tipo_obra"] = "residencial"
        elif any(w in texto.lower() for w in ["comercial", "loja", "escritório"]):
            dados["tipo_obra"] = "comercial"
        elif any(w in texto.lower() for w in ["industrial", "fábrica"]):
            dados["tipo_obra"] = "industrial"

        # Título resumido
        dados["titulo"] = texto[:200].strip()

        return dados if len(dados) > 1 else None

    def _deduplicar(self, results: List[ScraperResult]) -> List[ScraperResult]:
        seen = set()
        unique = []
        for r in results:
            key = r.fonte_ref or r.titulo[:50]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
