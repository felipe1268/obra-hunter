"""
ObraHunter - Schemas Pydantic para validação da API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import (
    TipoObra, FaseObra, PorteObra, FonteDados,
    StatusLead, StatusDecisor, TipoInteracao,
    FrequenciaBusca, TipoAlerta
)


# ==================== OBRA ====================

class ObraBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    bairro: Optional[str] = None
    cep: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tipo: TipoObra = TipoObra.RESIDENCIAL
    fase: FaseObra = FaseObra.DESCONHECIDA
    porte: PorteObra = PorteObra.DESCONHECIDO
    area_m2: Optional[float] = None
    valor_estimado: Optional[float] = None
    fonte: FonteDados
    fonte_url: Optional[str] = None
    fonte_ref: Optional[str] = None


class ObraCreate(ObraBase):
    pass


class ObraUpdate(BaseModel):
    titulo: Optional[str] = None
    status: Optional[StatusLead] = None
    tipo: Optional[TipoObra] = None
    fase: Optional[FaseObra] = None
    porte: Optional[PorteObra] = None
    score_oportunidade: Optional[float] = None


class ObraResponse(ObraBase):
    id: int
    status: StatusLead
    score_oportunidade: float
    alerta_enviado: bool
    data_encontrada: datetime
    data_atualizacao: datetime
    empresas: List["EmpresaResponse"] = []
    decisores: List["DecisorResponse"] = []

    class Config:
        from_attributes = True


class ObraListResponse(BaseModel):
    items: List[ObraResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== EMPRESA ====================

class EmpresaBase(BaseModel):
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    site: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaResponse(EmpresaBase):
    id: int
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    endereco_sede: Optional[str] = None
    cidade_sede: Optional[str] = None
    estado_sede: Optional[str] = None
    atividade_principal: Optional[str] = None
    situacao_cadastral: Optional[str] = None
    socios: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== DECISOR ====================

class DecisorBase(BaseModel):
    nome: str
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    linkedin_url: Optional[str] = None


class DecisorCreate(DecisorBase):
    obra_id: Optional[int] = None
    empresa_id: Optional[int] = None


class DecisorUpdate(BaseModel):
    status: Optional[StatusDecisor] = None
    nome: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None


class DecisorResponse(DecisorBase):
    id: int
    status: StatusDecisor
    cargo_score: float
    fonte_sugestao: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== INTERAÇÃO ====================

class InteracaoCreate(BaseModel):
    tipo: TipoInteracao
    notas: Optional[str] = None
    resultado: Optional[str] = None
    obra_id: int
    decisor_id: Optional[int] = None
    proxima_acao: Optional[datetime] = None


class InteracaoResponse(InteracaoCreate):
    id: int
    data: datetime

    class Config:
        from_attributes = True


# ==================== BUSCA AUTOMÁTICA ====================

class FiltrosBusca(BaseModel):
    estados: Optional[List[str]] = None
    cidades: Optional[List[str]] = None
    tipos: Optional[List[TipoObra]] = None
    fases: Optional[List[FaseObra]] = None
    portes: Optional[List[PorteObra]] = None
    fontes: Optional[List[FonteDados]] = None
    palavras_chave: Optional[List[str]] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None


class BuscaAutomaticaCreate(BaseModel):
    nome: str
    frequencia: FrequenciaBusca = FrequenciaBusca.DIARIA
    intervalo_minutos: Optional[int] = None
    filtros: FiltrosBusca
    score_minimo_alerta: float = 7.0
    alertas: Optional[List["ConfigAlertaCreate"]] = None


class BuscaAutomaticaResponse(BaseModel):
    id: int
    nome: str
    ativa: bool
    frequencia: FrequenciaBusca
    filtros: dict
    score_minimo_alerta: float
    total_execucoes: int
    total_obras_encontradas: int
    total_alertas_enviados: int
    ultima_execucao: Optional[datetime] = None
    proxima_execucao: Optional[datetime] = None
    created_at: datetime
    alertas: List["ConfigAlertaResponse"] = []

    class Config:
        from_attributes = True


class ConfigAlertaCreate(BaseModel):
    tipo: TipoAlerta
    destino: str
    ativo: bool = True


class ConfigAlertaResponse(ConfigAlertaCreate):
    id: int

    class Config:
        from_attributes = True


# ==================== EXECUÇÃO ====================

class ExecucaoResponse(BaseModel):
    id: int
    busca_id: int
    status: str
    obras_encontradas: int
    obras_novas: int
    alertas_enviados: int
    erro: Optional[str] = None
    duracao_segundos: Optional[float] = None
    inicio: datetime
    fim: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== DASHBOARD ====================

class DashboardStats(BaseModel):
    total_obras: int
    obras_novas_hoje: int
    obras_novas_semana: int
    total_empresas: int
    total_decisores: int
    decisores_validados: int
    buscas_ativas: int
    alertas_hoje: int
    score_medio: float
    obras_por_status: dict
    obras_por_tipo: dict
    obras_por_estado: dict
    obras_por_fonte: dict
    timeline_semanal: List[dict]


class AlertaOportunidade(BaseModel):
    obra: ObraResponse
    score: float
    motivo: str
    empresas: List[EmpresaResponse]
    decisores_sugeridos: int
    data_alerta: datetime
