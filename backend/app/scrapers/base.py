"""
ObraHunter - Base Scraper
Classe base para todos os scrapers com funcionalidades comuns
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScraperResult:
    """Resultado padronizado de qualquer scraper"""

    def __init__(
        self,
        titulo: str,
        fonte: str,
        fonte_url: Optional[str] = None,
        fonte_ref: Optional[str] = None,
        endereco: Optional[str] = None,
        cidade: Optional[str] = None,
        estado: Optional[str] = None,
        bairro: Optional[str] = None,
        cep: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        tipo_obra: Optional[str] = None,
        fase_obra: Optional[str] = None,
        area_m2: Optional[float] = None,
        valor_estimado: Optional[float] = None,
        empresa_nome: Optional[str] = None,
        empresa_cnpj: Optional[str] = None,
        empresa_site: Optional[str] = None,
        data_publicacao: Optional[datetime] = None,
        dados_extras: Optional[Dict] = None,
    ):
        self.titulo = titulo
        self.fonte = fonte
        self.fonte_url = fonte_url
        self.fonte_ref = fonte_ref
        self.endereco = endereco
        self.cidade = cidade
        self.estado = estado
        self.bairro = bairro
        self.cep = cep
        self.latitude = latitude
        self.longitude = longitude
        self.tipo_obra = tipo_obra
        self.fase_obra = fase_obra
        self.area_m2 = area_m2
        self.valor_estimado = valor_estimado
        self.empresa_nome = empresa_nome
        self.empresa_cnpj = empresa_cnpj
        self.empresa_site = empresa_site
        self.data_publicacao = data_publicacao
        self.dados_extras = dados_extras or {}

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BaseScraper(ABC):
    """Classe base para todos os scrapers"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.delay = settings.SCRAPER_DELAY_SECONDS
        self.max_retries = settings.SCRAPER_MAX_RETRIES
        self.timeout = settings.SCRAPER_TIMEOUT
        self.results: List[ScraperResult] = []
        self.errors: List[str] = []
        self.stats = {
            "pages_scraped": 0,
            "results_found": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    async def __aenter__(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """Faz request HTTP com retry e rate limiting"""
        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(self.delay)
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        self.stats["pages_scraped"] += 1
                        return await response.text()
                    elif response.status == 429:
                        wait_time = self.delay * (attempt + 2)
                        logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"HTTP {response.status} on {url}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                self.errors.append(f"{url}: {str(e)}")

        self.stats["errors"] += 1
        return None

    async def fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Faz request e retorna JSON"""
        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(self.delay)
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        self.stats["pages_scraped"] += 1
                        return await response.json()
            except Exception as e:
                logger.error(f"Error fetching JSON {url}: {e}")

        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML com BeautifulSoup"""
        return BeautifulSoup(html, "html.parser")

    @abstractmethod
    async def buscar(self, filtros: Dict[str, Any]) -> List[ScraperResult]:
        """Método principal de busca - implementado por cada scraper"""
        pass

    @abstractmethod
    def get_fonte(self) -> str:
        """Retorna o identificador da fonte"""
        pass

    async def executar(self, filtros: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o scraper e retorna resultados + estatísticas"""
        self.stats["start_time"] = datetime.utcnow()

        try:
            async with self:
                self.results = await self.buscar(filtros)
                self.stats["results_found"] = len(self.results)
        except Exception as e:
            logger.error(f"Scraper {self.get_fonte()} error: {e}")
            self.errors.append(str(e))
        finally:
            self.stats["end_time"] = datetime.utcnow()

        return {
            "fonte": self.get_fonte(),
            "results": [r.to_dict() for r in self.results],
            "stats": self.stats,
            "errors": self.errors,
        }
