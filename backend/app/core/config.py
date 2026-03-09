"""
ObraHunter - Configurações centrais do sistema
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ObraHunter"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "obra-hunter-secret-key-change-in-production")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/obrahunter"
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/obrahunter"
    )

    # Redis (para filas e cache)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Google Maps API
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")

    # Serviços externos
    RECEITA_WS_URL: str = "https://receitaws.com.br/v1/cnpj"

    # Scheduler - Configurações de automação
    SCHEDULER_ENABLED: bool = True
    BUSCA_DIARIA_HORA: int = 6  # Hora para executar busca diária (6h da manhã)
    BUSCA_CONTINUA_INTERVALO_MIN: int = 30  # Intervalo em minutos entre buscas contínuas
    MAX_CONCURRENT_SCRAPERS: int = 4  # Scrapers rodando em paralelo

    # Alertas
    ALERT_EMAIL_ENABLED: bool = True
    ALERT_WHATSAPP_ENABLED: bool = False
    ALERT_WEBHOOK_URL: Optional[str] = os.getenv("ALERT_WEBHOOK_URL")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")

    # Score de oportunidade (pesos para classificação)
    SCORE_PESO_PORTE: float = 0.3
    SCORE_PESO_FASE: float = 0.25
    SCORE_PESO_TIPO: float = 0.2
    SCORE_PESO_CONTATOS: float = 0.15
    SCORE_PESO_RECENCIA: float = 0.1
    SCORE_THRESHOLD_ALERTA: float = 7.0  # Score mínimo para disparar alerta

    # Rate limiting para scrapers
    SCRAPER_DELAY_SECONDS: float = 2.0  # Delay entre requests
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_TIMEOUT: int = 30

    # Paginação
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
