"""
ObraHunter - Scraper Google Maps
Busca canteiros de obra, construtoras e empreendimentos via Google Places API
"""
import logging
from typing import List, Dict, Any, Optional
from app.scrapers.base import BaseScraper, ScraperResult
from app.core.config import settings

logger = logging.getLogger(__name__)

# Queries de busca por tipo de obra
QUERIES_POR_TIPO = {
    "residencial": [
        "obra residencial",
        "construção residencial",
        "condomínio em construção",
        "empreendimento residencial lançamento",
        "prédio em construção",
    ],
    "comercial": [
        "obra comercial",
        "construção comercial",
        "galpão em construção",
        "shopping em construção",
        "centro comercial construção",
    ],
    "industrial": [
        "obra industrial",
        "construção industrial",
        "fábrica em construção",
        "parque industrial construção",
    ],
    "infraestrutura": [
        "obra de infraestrutura",
        "construção ponte",
        "obra viária",
        "pavimentação",
        "saneamento obra",
    ],
    "loteamento": [
        "loteamento em obras",
        "loteamento novo",
        "terreno loteamento construção",
    ],
    "geral": [
        "canteiro de obras",
        "construtora",
        "obra em andamento",
        "construção civil",
        "empreiteira",
    ],
}

# UFs do Brasil com coordenadas centrais para busca
ESTADOS_BR = {
    "AC": {"lat": -9.97, "lng": -67.81, "nome": "Acre"},
    "AL": {"lat": -9.66, "lng": -35.74, "nome": "Alagoas"},
    "AP": {"lat": 0.034, "lng": -51.07, "nome": "Amapá"},
    "AM": {"lat": -3.12, "lng": -60.02, "nome": "Amazonas"},
    "BA": {"lat": -12.97, "lng": -38.51, "nome": "Bahia"},
    "CE": {"lat": -3.72, "lng": -38.53, "nome": "Ceará"},
    "DF": {"lat": -15.80, "lng": -47.86, "nome": "Distrito Federal"},
    "ES": {"lat": -20.32, "lng": -40.34, "nome": "Espírito Santo"},
    "GO": {"lat": -16.68, "lng": -49.26, "nome": "Goiás"},
    "MA": {"lat": -2.53, "lng": -44.28, "nome": "Maranhão"},
    "MT": {"lat": -15.60, "lng": -56.10, "nome": "Mato Grosso"},
    "MS": {"lat": -20.44, "lng": -54.65, "nome": "Mato Grosso do Sul"},
    "MG": {"lat": -19.92, "lng": -43.94, "nome": "Minas Gerais"},
    "PA": {"lat": -1.46, "lng": -48.50, "nome": "Pará"},
    "PB": {"lat": -7.12, "lng": -34.86, "nome": "Paraíba"},
    "PR": {"lat": -25.43, "lng": -49.27, "nome": "Paraná"},
    "PE": {"lat": -8.05, "lng": -34.87, "nome": "Pernambuco"},
    "PI": {"lat": -5.09, "lng": -42.80, "nome": "Piauí"},
    "RJ": {"lat": -22.91, "lng": -43.17, "nome": "Rio de Janeiro"},
    "RN": {"lat": -5.79, "lng": -35.21, "nome": "Rio Grande do Norte"},
    "RS": {"lat": -30.03, "lng": -51.23, "nome": "Rio Grande do Sul"},
    "RO": {"lat": -8.76, "lng": -63.90, "nome": "Rondônia"},
    "RR": {"lat": 2.82, "lng": -60.67, "nome": "Roraima"},
    "SC": {"lat": -27.59, "lng": -48.55, "nome": "Santa Catarina"},
    "SP": {"lat": -23.55, "lng": -46.63, "nome": "São Paulo"},
    "SE": {"lat": -10.91, "lng": -37.07, "nome": "Sergipe"},
    "TO": {"lat": -10.18, "lng": -48.33, "nome": "Tocantins"},
}


class GoogleMapsScraper(BaseScraper):
    """
    Scraper que usa Google Places API para encontrar obras.
    Busca por termos relacionados a construção em regiões específicas.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def get_fonte(self) -> str:
        return "google_maps"

    async def buscar(self, filtros: Dict[str, Any]) -> List[ScraperResult]:
        results = []

        if not settings.GOOGLE_MAPS_API_KEY:
            logger.warning("Google Maps API key não configurada")
            self.errors.append("GOOGLE_MAPS_API_KEY não configurada")
            return results

        # Determinar estados para buscar
        estados = filtros.get("estados")
        if not estados:
            estados = list(ESTADOS_BR.keys())

        # Determinar queries baseado no tipo de obra
        tipos = filtros.get("tipos", ["geral"])
        queries = []
        for tipo in tipos:
            queries.extend(QUERIES_POR_TIPO.get(tipo, QUERIES_POR_TIPO["geral"]))
        queries = list(set(queries))  # Deduplica

        # Cidades específicas?
        cidades = filtros.get("cidades", [])

        for estado in estados:
            estado_info = ESTADOS_BR.get(estado, {})
            if not estado_info:
                continue

            for query in queries[:3]:  # Limita queries por estado para economizar API
                if cidades:
                    for cidade in cidades:
                        search_query = f"{query} {cidade} {estado}"
                        new_results = await self._search_places(
                            search_query, estado_info["lat"], estado_info["lng"], estado
                        )
                        results.extend(new_results)
                else:
                    search_query = f"{query} {estado_info['nome']}"
                    new_results = await self._search_places(
                        search_query, estado_info["lat"], estado_info["lng"], estado
                    )
                    results.extend(new_results)

        return self._deduplicar(results)

    async def _search_places(
        self, query: str, lat: float, lng: float, estado: str
    ) -> List[ScraperResult]:
        """Busca na Google Places API"""
        results = []
        url = f"{self.BASE_URL}/textsearch/json"
        params = {
            "query": query,
            "location": f"{lat},{lng}",
            "radius": 50000,  # 50km
            "language": "pt-BR",
            "key": settings.GOOGLE_MAPS_API_KEY,
        }

        data = await self.fetch_json(url, params)
        if not data or data.get("status") != "OK":
            return results

        for place in data.get("results", []):
            result = self._parse_place(place, estado)
            if result:
                results.append(result)

        # Pegar next page se existir
        next_token = data.get("next_page_token")
        if next_token:
            import asyncio
            await asyncio.sleep(2)  # Google exige delay para next_page_token
            params = {"pagetoken": next_token, "key": settings.GOOGLE_MAPS_API_KEY}
            data = await self.fetch_json(url, params)
            if data and data.get("status") == "OK":
                for place in data.get("results", []):
                    result = self._parse_place(place, estado)
                    if result:
                        results.append(result)

        return results

    def _parse_place(self, place: Dict, estado: str) -> Optional[ScraperResult]:
        """Converte resultado do Google Places para ScraperResult"""
        name = place.get("name", "")
        address = place.get("formatted_address", "")
        location = place.get("geometry", {}).get("location", {})

        # Filtrar resultados irrelevantes
        irrelevant = ["restaurante", "bar", "hotel", "farmácia", "mercado", "escola"]
        if any(word in name.lower() for word in irrelevant):
            return None

        # Extrair cidade do endereço
        parts = address.split(",")
        cidade = parts[-3].strip() if len(parts) >= 3 else ""
        bairro = parts[-4].strip() if len(parts) >= 4 else ""

        # Detectar tipo de obra pelo nome/categorias
        tipo_obra = self._detectar_tipo(name, place.get("types", []))

        return ScraperResult(
            titulo=name,
            fonte="google_maps",
            fonte_url=f"https://maps.google.com/?q={location.get('lat')},{location.get('lng')}",
            fonte_ref=place.get("place_id"),
            endereco=address,
            cidade=cidade,
            estado=estado,
            bairro=bairro,
            latitude=location.get("lat"),
            longitude=location.get("lng"),
            tipo_obra=tipo_obra,
            empresa_nome=name if self._is_empresa(place) else None,
            dados_extras={
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
                "types": place.get("types", []),
                "business_status": place.get("business_status"),
                "photos": len(place.get("photos", [])),
            },
        )

    def _detectar_tipo(self, name: str, types: List[str]) -> str:
        """Detecta tipo de obra baseado no nome e categorias"""
        name_lower = name.lower()
        if any(w in name_lower for w in ["residencial", "condomínio", "apartamento", "casa"]):
            return "residencial"
        if any(w in name_lower for w in ["comercial", "shopping", "loja", "galpão", "escritório"]):
            return "comercial"
        if any(w in name_lower for w in ["industrial", "fábrica", "indústria"]):
            return "industrial"
        if any(w in name_lower for w in ["loteamento", "terreno", "lote"]):
            return "loteamento"
        return "desconhecido"

    def _is_empresa(self, place: Dict) -> bool:
        """Verifica se o resultado é uma empresa (construtora/empreiteira)"""
        types = place.get("types", [])
        business_types = ["general_contractor", "construction_company", "real_estate_agency"]
        return any(t in types for t in business_types)

    def _deduplicar(self, results: List[ScraperResult]) -> List[ScraperResult]:
        """Remove resultados duplicados por place_id"""
        seen = set()
        unique = []
        for r in results:
            key = r.fonte_ref or f"{r.latitude}:{r.longitude}"
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
