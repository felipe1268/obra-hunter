"""
ObraHunter - API Routes
Todos os endpoints da API REST
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import (
    Obra, Empresa, Decisor, Interacao,
    BuscaAutomatica, ConfigAlerta, ExecucaoBusca,
    StatusLead, StatusDecisor, TipoObra, FonteDados
)
from app.schemas.schemas import (
    ObraCreate, ObraUpdate, ObraResponse, ObraListResponse,
    EmpresaResponse, DecisorCreate, DecisorUpdate, DecisorResponse,
    InteracaoCreate, InteracaoResponse,
    BuscaAutomaticaCreate, BuscaAutomaticaResponse,
    ExecucaoResponse, DashboardStats, FiltrosBusca,
)
from app.services.score import ScoreService
from app.tasks.scheduler import ObraHunterScheduler

router = APIRouter()
score_service = ScoreService()
scheduler = ObraHunterScheduler()


# ==================== OBRAS ====================

@router.get("/obras", response_model=ObraListResponse)
async def listar_obras(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[StatusLead] = None,
    tipo: Optional[TipoObra] = None,
    fonte: Optional[FonteDados] = None,
    estado: Optional[str] = None,
    cidade: Optional[str] = None,
    score_min: Optional[float] = None,
    busca: Optional[str] = None,
    ordenar: str = Query("score", regex="^(score|data|titulo)$"),
    db: AsyncSession = Depends(get_db),
):
    """Lista obras com filtros e paginação"""
    query = select(Obra).options(
        selectinload(Obra.empresas),
        selectinload(Obra.decisores),
    )

    # Aplicar filtros
    if status:
        query = query.where(Obra.status == status)
    if tipo:
        query = query.where(Obra.tipo == tipo)
    if fonte:
        query = query.where(Obra.fonte == fonte)
    if estado:
        query = query.where(Obra.estado == estado)
    if cidade:
        query = query.where(Obra.cidade.ilike(f"%{cidade}%"))
    if score_min:
        query = query.where(Obra.score_oportunidade >= score_min)
    if busca:
        query = query.where(
            Obra.titulo.ilike(f"%{busca}%") |
            Obra.endereco.ilike(f"%{busca}%") |
            Obra.cidade.ilike(f"%{busca}%")
        )

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Ordenar
    if ordenar == "score":
        query = query.order_by(Obra.score_oportunidade.desc())
    elif ordenar == "data":
        query = query.order_by(Obra.data_encontrada.desc())
    else:
        query = query.order_by(Obra.titulo)

    # Paginar
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    obras = result.scalars().all()

    return ObraListResponse(
        items=obras,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/obras/{obra_id}", response_model=ObraResponse)
async def detalhe_obra(obra_id: int, db: AsyncSession = Depends(get_db)):
    """Detalhe completo de uma obra"""
    result = await db.execute(
        select(Obra)
        .options(selectinload(Obra.empresas), selectinload(Obra.decisores))
        .where(Obra.id == obra_id)
    )
    obra = result.scalar_one_or_none()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    return obra


@router.patch("/obras/{obra_id}", response_model=ObraResponse)
async def atualizar_obra(
    obra_id: int, update: ObraUpdate, db: AsyncSession = Depends(get_db)
):
    """Atualiza status/dados de uma obra"""
    obra = await db.get(Obra, obra_id)
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(obra, field, value)

    obra.data_atualizacao = datetime.utcnow()
    await db.flush()
    return obra


# ==================== DECISORES ====================

@router.get("/obras/{obra_id}/decisores", response_model=List[DecisorResponse])
async def listar_decisores(obra_id: int, db: AsyncSession = Depends(get_db)):
    """Lista decisores sugeridos para uma obra"""
    result = await db.execute(
        select(Decisor).where(Decisor.obra_id == obra_id)
        .order_by(Decisor.cargo_score.desc())
    )
    return result.scalars().all()


@router.patch("/decisores/{decisor_id}", response_model=DecisorResponse)
async def atualizar_decisor(
    decisor_id: int, update: DecisorUpdate, db: AsyncSession = Depends(get_db)
):
    """Valida ou descarta um decisor sugerido"""
    decisor = await db.get(Decisor, decisor_id)
    if not decisor:
        raise HTTPException(status_code=404, detail="Decisor não encontrado")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(decisor, field, value)

    if update.status == StatusDecisor.VALIDADO:
        decisor.validated_at = datetime.utcnow()

    await db.flush()
    return decisor


# ==================== INTERAÇÕES ====================

@router.post("/interacoes", response_model=InteracaoResponse)
async def criar_interacao(
    data: InteracaoCreate, db: AsyncSession = Depends(get_db)
):
    """Registra uma interação com um lead"""
    interacao = Interacao(**data.model_dump())
    db.add(interacao)
    await db.flush()
    return interacao


@router.get("/obras/{obra_id}/interacoes", response_model=List[InteracaoResponse])
async def listar_interacoes(obra_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interacao).where(Interacao.obra_id == obra_id)
        .order_by(Interacao.data.desc())
    )
    return result.scalars().all()


# ==================== BUSCAS AUTOMÁTICAS ====================

@router.post("/buscas", response_model=BuscaAutomaticaResponse)
async def criar_busca_automatica(
    data: BuscaAutomaticaCreate, db: AsyncSession = Depends(get_db)
):
    """Cria nova busca automática recorrente"""
    busca = BuscaAutomatica(
        nome=data.nome,
        frequencia=data.frequencia,
        intervalo_minutos=data.intervalo_minutos,
        filtros=data.filtros.model_dump(),
        score_minimo_alerta=data.score_minimo_alerta,
        proxima_execucao=datetime.utcnow(),  # Executa imediatamente na primeira vez
    )
    db.add(busca)
    await db.flush()

    # Criar alertas
    if data.alertas:
        for alerta_data in data.alertas:
            alerta = ConfigAlerta(
                busca_id=busca.id,
                tipo=alerta_data.tipo,
                destino=alerta_data.destino,
                ativo=alerta_data.ativo,
            )
            db.add(alerta)

    await db.flush()
    return busca


@router.get("/buscas", response_model=List[BuscaAutomaticaResponse])
async def listar_buscas(db: AsyncSession = Depends(get_db)):
    """Lista todas as buscas automáticas"""
    result = await db.execute(
        select(BuscaAutomatica)
        .options(selectinload(BuscaAutomatica.alertas))
        .order_by(BuscaAutomatica.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/buscas/{busca_id}/toggle")
async def toggle_busca(busca_id: int, db: AsyncSession = Depends(get_db)):
    """Ativa/desativa uma busca automática"""
    busca = await db.get(BuscaAutomatica, busca_id)
    if not busca:
        raise HTTPException(status_code=404, detail="Busca não encontrada")
    busca.ativa = not busca.ativa
    await db.flush()
    return {"ativa": busca.ativa}


@router.post("/buscas/{busca_id}/executar")
async def executar_busca_agora(busca_id: int):
    """Força execução imediata de uma busca"""
    resultado = await scheduler.executar_busca(busca_id)
    return resultado


@router.get("/buscas/{busca_id}/execucoes", response_model=List[ExecucaoResponse])
async def listar_execucoes(
    busca_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    """Lista últimas execuções de uma busca"""
    result = await db.execute(
        select(ExecucaoBusca)
        .where(ExecucaoBusca.busca_id == busca_id)
        .order_by(ExecucaoBusca.inicio.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ==================== BUSCA MANUAL ====================

@router.post("/busca-manual")
async def busca_manual(filtros: FiltrosBusca):
    """Executa uma busca manual sem salvar como automática"""
    resultado = await scheduler.executar_busca_manual(filtros.model_dump())
    return resultado


# ==================== DASHBOARD ====================

@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(db: AsyncSession = Depends(get_db)):
    """Retorna estatísticas do dashboard"""
    agora = datetime.utcnow()
    hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    semana = hoje - timedelta(days=7)

    # Totais
    total_obras = (await db.execute(select(func.count(Obra.id)))).scalar() or 0
    obras_hoje = (await db.execute(
        select(func.count(Obra.id)).where(Obra.data_encontrada >= hoje)
    )).scalar() or 0
    obras_semana = (await db.execute(
        select(func.count(Obra.id)).where(Obra.data_encontrada >= semana)
    )).scalar() or 0
    total_empresas = (await db.execute(select(func.count(Empresa.id)))).scalar() or 0
    total_decisores = (await db.execute(select(func.count(Decisor.id)))).scalar() or 0
    decisores_validados = (await db.execute(
        select(func.count(Decisor.id)).where(Decisor.status == StatusDecisor.VALIDADO)
    )).scalar() or 0
    buscas_ativas = (await db.execute(
        select(func.count(BuscaAutomatica.id)).where(BuscaAutomatica.ativa == True)
    )).scalar() or 0
    score_medio = (await db.execute(
        select(func.avg(Obra.score_oportunidade))
    )).scalar() or 0

    # Obras por status
    status_result = await db.execute(
        select(Obra.status, func.count(Obra.id)).group_by(Obra.status)
    )
    obras_por_status = {str(row[0].value): row[1] for row in status_result}

    # Obras por tipo
    tipo_result = await db.execute(
        select(Obra.tipo, func.count(Obra.id)).group_by(Obra.tipo)
    )
    obras_por_tipo = {str(row[0].value): row[1] for row in tipo_result}

    # Obras por estado
    estado_result = await db.execute(
        select(Obra.estado, func.count(Obra.id))
        .where(Obra.estado != None)
        .group_by(Obra.estado)
        .order_by(func.count(Obra.id).desc())
        .limit(10)
    )
    obras_por_estado = {row[0]: row[1] for row in estado_result}

    # Obras por fonte
    fonte_result = await db.execute(
        select(Obra.fonte, func.count(Obra.id)).group_by(Obra.fonte)
    )
    obras_por_fonte = {str(row[0].value): row[1] for row in fonte_result}

    # Timeline semanal (últimos 7 dias)
    timeline = []
    for i in range(7):
        dia = hoje - timedelta(days=6 - i)
        dia_fim = dia + timedelta(days=1)
        count = (await db.execute(
            select(func.count(Obra.id)).where(
                and_(Obra.data_encontrada >= dia, Obra.data_encontrada < dia_fim)
            )
        )).scalar() or 0
        timeline.append({
            "data": dia.strftime("%d/%m"),
            "dia_semana": dia.strftime("%a"),
            "obras": count,
        })

    return DashboardStats(
        total_obras=total_obras,
        obras_novas_hoje=obras_hoje,
        obras_novas_semana=obras_semana,
        total_empresas=total_empresas,
        total_decisores=total_decisores,
        decisores_validados=decisores_validados,
        buscas_ativas=buscas_ativas,
        alertas_hoje=0,  # TODO: contar alertas do dia
        score_medio=round(score_medio, 2),
        obras_por_status=obras_por_status,
        obras_por_tipo=obras_por_tipo,
        obras_por_estado=obras_por_estado,
        obras_por_fonte=obras_por_fonte,
        timeline_semanal=timeline,
    )


# ==================== ALERTAS ====================

@router.get("/alertas/recentes")
async def alertas_recentes(
    limit: int = 20, db: AsyncSession = Depends(get_db)
):
    """Lista obras de alto score encontradas recentemente"""
    result = await db.execute(
        select(Obra)
        .options(selectinload(Obra.empresas))
        .where(Obra.score_oportunidade >= 7.0)
        .order_by(Obra.data_encontrada.desc())
        .limit(limit)
    )
    obras = result.scalars().all()
    return [
        {
            "obra": obra,
            "score": obra.score_oportunidade,
            "classificacao": score_service.classificar_oportunidade(obra.score_oportunidade),
            "motivo": score_service.gerar_motivo_alerta(
                {
                    "porte": obra.porte.value if obra.porte else "",
                    "fase": obra.fase.value if obra.fase else "",
                    "tipo": obra.tipo.value if obra.tipo else "",
                    "valor_estimado": obra.valor_estimado,
                    "area_m2": obra.area_m2,
                },
                obra.score_oportunidade,
            ),
        }
        for obra in obras
    ]
