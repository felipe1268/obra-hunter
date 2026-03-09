"""
ObraHunter - Serviço de Notificações In-App
"""
import logging
from typing import List, Dict
from datetime import datetime
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Usuario, Notificacao, TipoNotificacao
from app.services.score import ScoreService

logger = logging.getLogger(__name__)
score_service = ScoreService()


class NotificacaoService:

    async def criar(self, db: AsyncSession, usuario_id: int, tipo: TipoNotificacao, titulo: str, mensagem: str = None, obra_id: int = None, score: float = None, dados: dict = None) -> Notificacao:
        notif = Notificacao(usuario_id=usuario_id, tipo=tipo, titulo=titulo, mensagem=mensagem, obra_id=obra_id, score=score, dados=dados)
        db.add(notif)
        await db.flush()
        return notif

    async def notificar_todos(self, db: AsyncSession, tipo: TipoNotificacao, titulo: str, mensagem: str = None, obra_id: int = None, score: float = None, dados: dict = None, estado_obra: str = None, tipo_obra: str = None) -> int:
        result = await db.execute(select(Usuario).where(Usuario.ativo == True, Usuario.notificacoes_ativas == True))
        users = result.scalars().all()
        count = 0
        for user in users:
            if estado_obra and user.estados_interesse and estado_obra not in user.estados_interesse:
                continue
            if tipo_obra and user.tipos_interesse and tipo_obra not in user.tipos_interesse:
                continue
            if score and user.score_minimo_notificacao and score < user.score_minimo_notificacao:
                continue
            await self.criar(db, user.id, tipo, titulo, mensagem, obra_id, score, dados)
            count += 1
        return count

    async def notificar_nova_obra(self, db: AsyncSession, obra_data: dict, score_val: float) -> int:
        motivo = score_service.gerar_motivo_alerta(obra_data, score_val)
        if score_val >= 8.5:
            titulo = f"🔥 Oportunidade Quente! Score {score_val}/10"
            tipo = TipoNotificacao.OPORTUNIDADE
        elif score_val >= 7.0:
            titulo = f"⭐ Boa Oportunidade — Score {score_val}/10"
            tipo = TipoNotificacao.OBRA_NOVA
        else:
            titulo = f"📋 Nova Obra — Score {score_val}/10"
            tipo = TipoNotificacao.OBRA_NOVA

        mensagem = f"{obra_data.get('titulo', '')}\n📍 {obra_data.get('cidade', '')} - {obra_data.get('estado', '')}\n💡 {motivo}"
        return await self.notificar_todos(db, tipo, titulo, mensagem, obra_data.get("id"), score_val, estado_obra=obra_data.get("estado"), tipo_obra=obra_data.get("tipo"))

    async def notificar_busca_concluida(self, db: AsyncSession, nome: str, obras_novas: int, duracao: float) -> int:
        if obras_novas == 0:
            return 0
        return await self.notificar_todos(db, TipoNotificacao.BUSCA_CONCLUIDA, f"🔍 Busca '{nome}' concluída", f"{obras_novas} obras novas em {duracao:.0f}s")

    async def listar(self, db: AsyncSession, usuario_id: int, apenas_nao_lidas: bool = False, limit: int = 50) -> List[Notificacao]:
        query = select(Notificacao).where(Notificacao.usuario_id == usuario_id).order_by(Notificacao.created_at.desc()).limit(limit)
        if apenas_nao_lidas:
            query = query.where(Notificacao.lida == False)
        return (await db.execute(query)).scalars().all()

    async def contar_nao_lidas(self, db: AsyncSession, usuario_id: int) -> int:
        return (await db.execute(select(func.count(Notificacao.id)).where(and_(Notificacao.usuario_id == usuario_id, Notificacao.lida == False)))).scalar() or 0

    async def marcar_lida(self, db: AsyncSession, notif_id: int, usuario_id: int) -> bool:
        result = await db.execute(update(Notificacao).where(and_(Notificacao.id == notif_id, Notificacao.usuario_id == usuario_id)).values(lida=True, lida_em=datetime.utcnow()))
        await db.flush()
        return result.rowcount > 0

    async def marcar_todas_lidas(self, db: AsyncSession, usuario_id: int) -> int:
        result = await db.execute(update(Notificacao).where(and_(Notificacao.usuario_id == usuario_id, Notificacao.lida == False)).values(lida=True, lida_em=datetime.utcnow()))
        await db.flush()
        return result.rowcount

    async def resumo(self, db: AsyncSession, usuario_id: int) -> dict:
        total = await self.contar_nao_lidas(db, usuario_id)
        urgentes = (await db.execute(select(func.count(Notificacao.id)).where(and_(Notificacao.usuario_id == usuario_id, Notificacao.lida == False, Notificacao.score >= 8.5)))).scalar() or 0
        return {"total_nao_lidas": total, "urgentes": urgentes}
