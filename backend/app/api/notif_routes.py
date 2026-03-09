"""
ObraHunter - Rotas de Notificações
Centro de notificações in-app do painel
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.notificacoes import NotificacaoService
from app.models.models import TipoNotificacao

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])
notif_service = NotificacaoService()


class NotificacaoResponse(BaseModel):
    id: int
    tipo: TipoNotificacao
    titulo: str
    mensagem: Optional[str] = None
    lida: bool
    obra_id: Optional[int] = None
    score: Optional[float] = None
    icone: Optional[str] = None
    dados: Optional[dict] = None
    created_at: datetime
    lida_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificacaoContagem(BaseModel):
    total: int
    nao_lidas: int


@router.get("", response_model=List[NotificacaoResponse])
async def listar_notificacoes(
    apenas_nao_lidas: bool = False,
    limit: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista notificações do usuário logado"""
    return await notif_service.get_notificacoes(
        db, user.id, apenas_nao_lidas, limit
    )


@router.get("/contagem", response_model=NotificacaoContagem)
async def contagem_notificacoes(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna contagem de notificações (para badge no sino)"""
    nao_lidas = await notif_service.contar_nao_lidas(db, user.id)
    return NotificacaoContagem(
        total=nao_lidas + 10,  # Placeholder
        nao_lidas=nao_lidas,
    )


@router.patch("/{notificacao_id}/lida")
async def marcar_lida(
    notificacao_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca uma notificação como lida"""
    ok = await notif_service.marcar_como_lida(db, notificacao_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"ok": True}


@router.patch("/marcar-todas-lidas")
async def marcar_todas_lidas(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca todas as notificações como lidas"""
    count = await notif_service.marcar_todas_lidas(db, user.id)
    return {"ok": True, "marcadas": count}
