"""
ObraHunter - Modelos do banco de dados
VersÃ£o completa com multi-usuÃ¡rio, notificaÃ§Ãµes in-app e times
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# ==================== ENUMS ====================

class TipoObra(str, enum.Enum):
    RESIDENCIAL = "residencial"
    COMERCIAL = "comercial"
    INDUSTRIAL = "industrial"
    INFRAESTRUTURA = "infraestrutura"
    LOTEAMENTO = "loteamento"
    REFORMA = "reforma"
    INSTITUCIONAL = "institucional"
    MISTO = "misto"

class FaseObra(str, enum.Enum):
    APROVACAO = "aprovacao"
    FUNDACAO = "fundacao"
    ESTRUTURA = "estrutura"
    ACABAMENTO = "acabamento"
    ENTREGA = "entrega"
    DESCONHECIDA = "desconhecida"

class PorteObra(str, enum.Enum):
    PEQUENO = "pequeno"
    MEDIO = "medio"
    GRANDE = "grande"
    DESCONHECIDO = "desconhecido"

class FonteDados(str, enum.Enum):
    DIARIO_OFICIAL = "diario_oficial"
    LICITACAO = "licitacao"
    CONSTRUTORA = "construtora"
    GOOGLE_MAPS = "google_maps"
    MANUAL = "manual"

class StatusLead(str, enum.Enum):
    NOVO = "novo"
    ENRIQUECIDO = "enriquecido"
    CONTATO_ENCONTRADO = "contato_encontrado"
    EM_PROSPECCAO = "em_prospeccao"
    CONTATADO = "contatado"
    EM_NEGOCIACAO = "em_negociacao"
    CONVERTIDO = "convertido"
    DESCARTADO = "descartado"

class StatusDecisor(str, enum.Enum):
    SUGERIDO = "sugerido"
    VALIDADO = "validado"
    DESCARTADO = "descartado"

class TipoInteracao(str, enum.Enum):
    NOTA = "nota"
    LIGACAO = "ligacao"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    REUNIAO = "reuniao"
    VISITA = "visita"

class FrequenciaBusca(str, enum.Enum):
    CONTINUA = "continua"
    DIARIA = "diaria"
    SEMANAL = "semanal"
    PERSONALIZADA = "personalizada"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    GERENTE = "gerente"
    VENDEDOR = "vendedor"

class TipoNotificacao(str, enum.Enum):
    OBRA_NOVA = "obra_nova"
    OPORTUNIDADE = "oportunidade"
    BUSCA_CONCLUIDA = "busca_concluida"
    DECISOR_ENCONTRADO = "decisor_encontrado"
    LEMBRETE = "lembrete"
    SISTEMA = "sistema"


# ==================== ASSOCIATIVAS ====================

obra_empresa = Table(
    "obra_empresa", Base.metadata,
    Column("obra_id", Integer, ForeignKey("obras.id", ondelete="CASCADE"), primary_key=True),
    Column("empresa_id", Integer, ForeignKey("empresas.id", ondelete="CASCADE"), primary_key=True),
    Column("papel", String(50), default="construtora"),
    Column("created_at", DateTime, default=datetime.utcnow),
)


# ==================== USUÃRIOS E NOTIFICAÃÃES ====================

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(300), unique=True, nullable=False, index=True)
    senha_hash = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VENDEDOR)
    ativo = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)

    # PreferÃªncias de notificaÃ§Ã£o
    notificacoes_ativas = Column(Boolean, default=True)
    score_minimo_notificacao = Column(Float, default=7.0)
    estados_interesse = Column(JSON, nullable=True)
    tipos_interesse = Column(JSON, nullable=True)

    # Datas
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    notificacoes = relationship("Notificacao", back_populates="usuario", cascade="all, delete-orphan")
    interacoes = relationship("Interacao", back_populates="usuario")
    obras_atribuidas = relationship("Obra", back_populates="responsavel")


class Notificacao(Base):
    """NotificaÃ§Ãµes in-app â centro de alertas do painel"""
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)

    tipo = Column(Enum(TipoNotificacao), nullable=False)
    titulo = Column(String(300), nullable=False)
    mensagem = Column(Text, nullable=True)
    lida = Column(Boolean, default=False, index=True)

    # ReferÃªncia Ã  obra
    obra_id = Column(Integer, ForeignKey("obras.id", ondelete="SET NULL"), nullable=True)
    score = Column(Float, nullable=True)
    icone = Column(String(50), nullable=True)  # nome do Ã­cone lucide

    # Dados extras
    dados = Column(JSON, nullable=True)

    # Datas
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    lida_em = Column(DateTime, nullable=True)

    # Relationships
    usuario = relationship("Usuario", back_populates="notificacoes")
    obra = relationship("Obra")

    __table_args__ = (
        Index("ix_notif_usuario_lida", "usuario_id", "lida"),
        Index("ix_notif_created", "created_at"),
    )


# ==================== OBRAS ====================

class Obra(Base):
    __tablename__ = "obras"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(500), nullable=False)
    descricao = Column(Text, nullable=True)

    endereco = Column(String(500), nullable=True)
    cidade = Column(String(200), nullable=True, index=True)
    estado = Column(String(2), nullable=True, index=True)
    bairro = Column(String(200), nullable=True)
    cep = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    tipo = Column(Enum(TipoObra), default=TipoObra.RESIDENCIAL, index=True)
    fase = Column(Enum(FaseObra), default=FaseObra.DESCONHECIDA, index=True)
    porte = Column(Enum(PorteObra), default=PorteObra.DESCONHECIDO)
    area_m2 = Column(Float, nullable=True)
    valor_estimado = Column(Float, nullable=True)

    fonte = Column(Enum(FonteDados), nullable=False, index=True)
    fonte_url = Column(String(1000), nullable=True)
    fonte_ref = Column(String(200), nullable=True)

    status = Column(Enum(StatusLead), default=StatusLead.NOVO, index=True)
    score_oportunidade = Column(Float, default=0.0, index=True)
    notificacao_enviada = Column(Boolean, default=False)

    # Vendedor responsÃ¡vel
    responsavel_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    data_encontrada = Column(DateTime, default=datetime.utcnow, index=True)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_publicacao = Column(DateTime, nullable=True)
    dados_extras = Column(JSON, nullable=True)

    empresas = relationship("Empresa", secondary=obra_empresa, back_populates="obras")
    decisores = relationship("Decisor", back_populates="obra", cascade="all, delete-orphan")
    interacoes = relationship("Interacao", back_populates="obra", cascade="all, delete-orphan")
    responsavel = relationship("Usuario", back_populates="obras_atribuidas")

    __table_args__ = (
        Index("ix_obra_cidade_tipo", "cidade", "tipo"),
        Index("ix_obra_estado_tipo", "estado", "tipo"),
        Index("ix_obra_score", "score_oportunidade", postgresql_using="btree"),
        UniqueConstraint("fonte", "fonte_ref", name="uq_obra_fonte_ref"),
    )


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), unique=True, nullable=True, index=True)
    razao_social = Column(String(500), nullable=True)
    nome_fantasia = Column(String(500), nullable=True)
    site = Column(String(500), nullable=True)
    email = Column(String(300), nullable=True)
    telefone = Column(String(50), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    instagram = Column(String(200), nullable=True)
    facebook = Column(String(200), nullable=True)
    linkedin = Column(String(200), nullable=True)
    endereco_sede = Column(String(500), nullable=True)
    cidade_sede = Column(String(200), nullable=True)
    estado_sede = Column(String(2), nullable=True)
    porte_empresa = Column(String(50), nullable=True)
    atividade_principal = Column(String(500), nullable=True)
    situacao_cadastral = Column(String(50), nullable=True)
    socios = Column(JSON, nullable=True)
    dados_extras = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    obras = relationship("Obra", secondary=obra_empresa, back_populates="empresas")
    decisores = relationship("Decisor", back_populates="empresa")


class Decisor(Base):
    __tablename__ = "decisores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(300), nullable=False)
    cargo = Column(String(200), nullable=True)
    cargo_score = Column(Float, default=0.0)
    email = Column(String(300), nullable=True)
    telefone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    status = Column(Enum(StatusDecisor), default=StatusDecisor.SUGERIDO)
    fonte_sugestao = Column(String(100), nullable=True)
    obra_id = Column(Integer, ForeignKey("obras.id", ondelete="SET NULL"), nullable=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)

    obra = relationship("Obra", back_populates="decisores")
    empresa = relationship("Empresa", back_populates="decisores")
    interacoes = relationship("Interacao", back_populates="decisor")


class Interacao(Base):
    __tablename__ = "interacoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoInteracao), nullable=False)
    notas = Column(Text, nullable=True)
    resultado = Column(String(200), nullable=True)
    obra_id = Column(Integer, ForeignKey("obras.id", ondelete="CASCADE"))
    decisor_id = Column(Integer, ForeignKey("decisores.id", ondelete="SET NULL"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    data = Column(DateTime, default=datetime.utcnow)
    proxima_acao = Column(DateTime, nullable=True)

    obra = relationship("Obra", back_populates="interacoes")
    decisor = relationship("Decisor", back_populates="interacoes")
    usuario = relationship("Usuario", back_populates="interacoes")


class BuscaAutomatica(Base):
    __tablename__ = "buscas_automaticas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    ativa = Column(Boolean, default=True, index=True)
    frequencia = Column(Enum(FrequenciaBusca), default=FrequenciaBusca.DIARIA)
    intervalo_minutos = Column(Integer, nullable=True)
    filtros = Column(JSON, nullable=False)
    score_minimo_alerta = Column(Float, default=7.0)
    criado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    total_execucoes = Column(Integer, default=0)
    total_obras_encontradas = Column(Integer, default=0)
    total_alertas_enviados = Column(Integer, default=0)
    ultima_execucao = Column(DateTime, nullable=True)
    proxima_execucao = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    execucoes = relationship("ExecucaoBusca", back_populates="busca", cascade="all, delete-orphan")
    alertas = relationship("ConfigAlerta", back_populates="busca", cascade="all, delete-orphan")


class ExecucaoBusca(Base):
    __tablename__ = "execucoes_busca"

    id = Column(Integer, primary_key=True, index=True)
    busca_id = Column(Integer, ForeignKey("buscas_automaticas.id", ondelete="CASCADE"))
    status = Column(String(50), default="running")
    obras_encontradas = Column(Integer, default=0)
    obras_novas = Column(Integer, default=0)
    alertas_enviados = Column(Integer, default=0)
    erro = Column(Text, nullable=True)
    duracao_segundos = Column(Float, nullable=True)
    fontes_consultadas = Column(JSON, nullable=True)
    inicio = Column(DateTime, default=datetime.utcnow)
    fim = Column(DateTime, nullable=True)

    busca = relationship("BuscaAutomatica", back_populates="execucoes")


class ConfigAlerta(Base):
    __tablename__ = "config_alertas"

    id = Column(Integer, primary_key=True, index=True)
    busca_id = Column(Integer, ForeignKey("buscas_automaticas.id", ondelete="CASCADE"))
    tipo = Column(String(50), nullable=False)
    destino = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    busca = relationship("BuscaAutomatica", back_populates="alertas")
