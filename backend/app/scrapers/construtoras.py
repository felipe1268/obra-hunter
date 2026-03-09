"""
ObraHunter - Scraper Construtoras
Busca lançamentos e obras em sites de construtoras e marketplaces imobiliários
"""
import re
import logging
from typing import List, Dict, Any, Optional
from app.scrapers.base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)

# Top construtoras do Brasil (fontes de lançamentos)
TOP_CONSTRUTORAS = [
    {"nome": "MRV", "site": "https://www.mrv.com.br", "lancamentos_url": "https://www.mrv.com.br/imoveis"},
    {"nome": "Cyrela", "site": "https://www.cyrela.com.br", "lancamentos_url": "https://www.cyrela.com.br/imoveis"},
    {"nome": "Direcional", "site": "https://www.direcional.com.br"},
    {"nome": "Tenda", "site": "https://www.tenda.com"},
    {"nome": "Even", "site": "https://www.even.com.br"},
    {"nome": "EZTec", "site": "https://www.eztec.com.br"},
    {"nome": "Cury", "site": "https://www.cfranciscocury.com.br"},
    {"nome": "Trisul", "site": "https://www.trisul.com.br"},
    {"nome": "Plano&Plano", "site": "https://www.planoeplano.com.br"},
    {"nome": "Gafisa", "site": "https://www.gafisa.com.br"},
    {"nome": "Helbor", "site": "https://www.helbor.com.br"},
    {"nome": "Moura Dubeux", "site": "https://www.mouradubeux.com.br"},
    {"nome": "Patrimar", "site": "https://www.patrimar.com.br"},
    {"nome": "Mitre", "site": "https://www.mitrerealty.com.br"},
    {"nome": "Melnick", "site": "https://www.melnick.com.br"},
]

# Marketplaces imobiliários
MARKETPLACES = [
    {
        "nome": "VivaReal",
        "url": "https://www.vivareal.com.br",
        "busca_template": "https://www.vivareal.com.br/venda/{estado}/{cidade}/apartamento_residencial/",
    },
    {
        "nome": "Zap Imóveis",
        "url": "https://www.zapimoveis.com.br",
    },
    {
        "nome": "Imovelweb",
        "url": "https://www.imovelweb.com.br",
    },
    {
        "nome": "OLX Imóveis",
        "url": "https://www.olx.com.br/imoveis",
    },
]


class ConstrutorasScraper(BaseScraper):
    """
    Scraper para sites de construtoras e marketplaces.
    Busca lançamentos, obras em andamento e empreendimentos novos.
    """

    def get_fonte(self) -> str:
        return "construtora"

    async def buscar(self, filtros: Dict[str, Any]) -> List[ScraperResult]:
        results = []

        # Buscar em sites de construtoras
        results.extend(await self._buscar_construtoras(filtros))

        # Buscar em marketplaces
        results.extend(await self._buscar_marketplaces(filtros))

        # Busca Google (fallback eficiente)
        results.extend(await self._busca_google_lancamentos(filtros))

        return self._deduplicar(results)

    async def _buscar_construtoras(self, filtros: Dict) -> List[ScraperResult]:
        """Busca lançamentos nos sites das top construtoras"""
        results = []
        estados = filtros.get("estados", [])
        cidades = filtros.get("cidades", [])

        for construtora in TOP_CONSTRUTORAS:
            url = construtora.get("lancamentos_url", construtora["site"])
            html = await self.fetch(url)
            if not html:
                continue

            soup = self.parse_html(html)
            empreendimentos = self._parse_site_construtora(soup, construtora)

            for emp in empreendimentos:
                # Filtrar por localização se especificado
                if estados and emp.estado not in estados:
                    continue
                if cidades and emp.cidade not in [c.lower() for c in cidades]:
                    continue
                results.append(emp)

        return results

    def _parse_site_construtora(
        self, soup, construtora: Dict
    ) -> List[ScraperResult]:
        """Parse genérico para sites de construtoras"""
        results = []

        # Buscar cards de empreendimentos (padrões comuns)
        selectors = [
            "div[class*='empreendimento']",
            "div[class*='imovel']",
            "div[class*='property']",
            "div[class*='card']",
            "article[class*='empreendimento']",
            "a[class*='property']",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        for item in items[:20]:  # Limita a 20 por construtora
            try:
                # Extrair título
                title_tag = item.find(["h2", "h3", "h4", "span"], class_=re.compile(r"title|name|nome"))
                titulo = title_tag.get_text(strip=True) if title_tag else ""

                # Extrair endereço/localização
                addr_tag = item.find(["p", "span", "div"], class_=re.compile(r"address|endereco|local|bairro"))
                endereco = addr_tag.get_text(strip=True) if addr_tag else ""

                # Extrair link
                link_tag = item.find("a")
                link = link_tag.get("href", "") if link_tag else ""
                if link and not link.startswith("http"):
                    link = construtora["site"].rstrip("/") + "/" + link.lstrip("/")

                # Extrair status/fase
                status_tag = item.find(["span", "div"], class_=re.compile(r"status|fase|stage|badge"))
                status = status_tag.get_text(strip=True) if status_tag else ""

                if titulo:
                    cidade_detectada, estado_detectado = self._extrair_localizacao(endereco)

                    results.append(ScraperResult(
                        titulo=f"{titulo} - {construtora['nome']}",
                        fonte="construtora",
                        fonte_url=link,
                        fonte_ref=f"{construtora['nome']}:{titulo[:50]}",
                        endereco=endereco,
                        cidade=cidade_detectada,
                        estado=estado_detectado,
                        tipo_obra="residencial",  # Construtoras = predominantemente residencial
                        fase_obra=self._detectar_fase(status),
                        empresa_nome=construtora["nome"],
                        empresa_site=construtora["site"],
                        dados_extras={
                            "construtora": construtora["nome"],
                            "status_original": status,
                        },
                    ))
            except Exception as e:
                logger.debug(f"Error parsing item from {construtora['nome']}: {e}")

        return results

    async def _buscar_marketplaces(self, filtros: Dict) -> List[ScraperResult]:
        """Busca lançamentos em marketplaces imobiliários"""
        results = []
        estados = filtros.get("estados", ["sp", "rj", "mg"])

        for marketplace in MARKETPLACES[:2]:  # Top 2 marketplaces
            for estado in estados:
                url = f"{marketplace['url']}/venda/{estado.lower()}"
                params = {"tipo": "lancamento", "ordenar": "mais-recentes"}
                html = await self.fetch(url, params)
                if html:
                    parsed = self._parse_marketplace(html, marketplace["nome"])
                    results.extend(parsed)

        return results

    def _parse_marketplace(self, html: str, marketplace_nome: str) -> List[ScraperResult]:
        """Parse genérico de resultados de marketplace"""
        results = []
        soup = self.parse_html(html)

        selectors = [
            "div[class*='listing']",
            "div[class*='card']",
            "article[class*='property']",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        for item in items[:15]:
            try:
                title_tag = item.find(["h2", "h3", "a"], class_=re.compile(r"title|name"))
                addr_tag = item.find(["p", "span"], class_=re.compile(r"address|location"))
                price_tag = item.find(["p", "span", "div"], class_=re.compile(r"price|valor"))

                titulo = title_tag.get_text(strip=True) if title_tag else ""
                endereco = addr_tag.get_text(strip=True) if addr_tag else ""
                preco_texto = price_tag.get_text(strip=True) if price_tag else ""

                valor = self._parse_valor(preco_texto)
                cidade, estado = self._extrair_localizacao(endereco)

                if titulo:
                    results.append(ScraperResult(
                        titulo=titulo,
                        fonte="construtora",
                        fonte_url=marketplace_nome,
                        endereco=endereco,
                        cidade=cidade,
                        estado=estado,
                        tipo_obra="residencial",
                        valor_estimado=valor,
                        dados_extras={"marketplace": marketplace_nome},
                    ))
            except Exception as e:
                logger.debug(f"Error parsing marketplace item: {e}")

        return results

    async def _busca_google_lancamentos(self, filtros: Dict) -> List[ScraperResult]:
        """Busca Google por lançamentos imobiliários recentes"""
        results = []
        estados = filtros.get("estados", ["SP", "RJ"])
        tipos = filtros.get("tipos", ["residencial"])

        queries = []
        for tipo in tipos:
            for estado in estados[:5]:
                queries.append(f"lançamento imobiliário {tipo} {estado} 2025")
                queries.append(f"obra nova {tipo} {estado} em construção")

        for query in queries[:6]:  # Limita queries
            html = await self.fetch(
                "https://www.google.com/search",
                params={"q": query, "num": 10}
            )
            if html:
                soup = self.parse_html(html)
                for g in soup.find_all("div", class_="g"):
                    title_tag = g.find("h3")
                    link_tag = g.find("a")
                    if title_tag and link_tag:
                        title = title_tag.get_text()
                        link = link_tag.get("href", "")
                        if self._is_lancamento(title):
                            results.append(ScraperResult(
                                titulo=title,
                                fonte="construtora",
                                fonte_url=link,
                                tipo_obra="residencial",
                            ))

        return results

    def _detectar_fase(self, status: str) -> str:
        """Detecta fase da obra pelo status"""
        s = status.lower()
        if any(w in s for w in ["lançamento", "breve", "pré-lançamento", "projeto"]):
            return "aprovacao"
        if any(w in s for w in ["fundação", "início", "terraplanagem"]):
            return "fundacao"
        if any(w in s for w in ["estrutura", "construção", "obra", "andamento"]):
            return "estrutura"
        if any(w in s for w in ["acabamento", "finalização"]):
            return "acabamento"
        if any(w in s for w in ["pronto", "entrega", "concluído"]):
            return "entrega"
        return "desconhecida"

    def _extrair_localizacao(self, texto: str) -> tuple:
        """Extrai cidade e estado de um texto de endereço"""
        # Padrão: "Bairro, Cidade - UF" ou "Cidade/UF"
        match = re.search(r'([A-Za-zÀ-ÿ\s]+)\s*[-/]\s*([A-Z]{2})', texto)
        if match:
            return match.group(1).strip(), match.group(2)
        return "", ""

    def _parse_valor(self, texto: str) -> Optional[float]:
        """Parse valor monetário de texto"""
        match = re.search(r'R\$\s*([\d.,]+)', texto)
        if match:
            valor_str = match.group(1).replace(".", "").replace(",", ".")
            try:
                return float(valor_str)
            except ValueError:
                pass
        return None

    def _is_lancamento(self, texto: str) -> bool:
        """Verifica se texto refere a lançamento/obra"""
        keywords = ["lançamento", "obra", "construção", "empreendimento", "condomínio"]
        return any(kw in texto.lower() for kw in keywords)

    def _deduplicar(self, results: List[ScraperResult]) -> List[ScraperResult]:
        seen = set()
        unique = []
        for r in results:
            key = r.fonte_ref or r.titulo[:60]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
