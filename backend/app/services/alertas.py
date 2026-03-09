"""
ObraHunter - Serviço de Alertas
Envia notificações quando obras com bom score são encontradas
"""
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertaService:
    """Serviço de envio de alertas multi-canal"""

    async def enviar_alerta(
        self,
        tipo: str,
        destino: str,
        obra_data: Dict,
        score: float,
        motivo: str,
    ) -> bool:
        """Envia alerta por canal específico"""
        try:
            if tipo == "email":
                return await self.enviar_email(destino, obra_data, score, motivo)
            elif tipo == "webhook":
                return await self.enviar_webhook(destino, obra_data, score, motivo)
            elif tipo == "push":
                return await self.enviar_push(destino, obra_data, score, motivo)
            elif tipo == "whatsapp":
                return await self.enviar_whatsapp(destino, obra_data, score, motivo)
            else:
                logger.warning(f"Tipo de alerta desconhecido: {tipo}")
                return False
        except Exception as e:
            logger.error(f"Erro enviando alerta {tipo} para {destino}: {e}")
            return False

    async def enviar_email(
        self,
        destino: str,
        obra_data: Dict,
        score: float,
        motivo: str,
    ) -> bool:
        """Envia alerta por email"""
        if not settings.SMTP_USER:
            logger.warning("SMTP não configurado")
            return False

        titulo = obra_data.get("titulo", "Nova obra encontrada")
        cidade = obra_data.get("cidade", "")
        estado = obra_data.get("estado", "")
        tipo = obra_data.get("tipo", "")
        fase = obra_data.get("fase", "")
        endereco = obra_data.get("endereco", "")
        empresa = obra_data.get("empresa_nome", "Não identificada")

        subject = f"🏗️ ObraHunter | Nova Oportunidade (Score {score}/10) — {titulo[:50]}"

        html_body = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; border-radius: 16px 16px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🏗️ Nova Oportunidade</h1>
                <p style="margin: 10px 0 0; opacity: 0.8; font-size: 14px;">ObraHunter encontrou uma obra que pode te interessar</p>
            </div>

            <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 16px 16px;">
                <div style="background: {'#ff4444' if score >= 8 else '#ff9800' if score >= 6 else '#4caf50'}; color: white; display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-bottom: 20px;">
                    Score: {score}/10
                </div>

                <h2 style="margin: 0 0 20px; color: #1a1a2e; font-size: 20px;">{titulo}</h2>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="border-bottom: 1px solid #f0f0f0;">
                        <td style="padding: 10px 0; color: #666; width: 130px;">📍 Localização</td>
                        <td style="padding: 10px 0; font-weight: 500;">{endereco or f'{cidade} - {estado}'}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f0f0f0;">
                        <td style="padding: 10px 0; color: #666;">🏢 Tipo</td>
                        <td style="padding: 10px 0; font-weight: 500;">{tipo.capitalize()}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f0f0f0;">
                        <td style="padding: 10px 0; color: #666;">⚙️ Fase</td>
                        <td style="padding: 10px 0; font-weight: 500;">{fase.capitalize()}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f0f0f0;">
                        <td style="padding: 10px 0; color: #666;">🏭 Empresa</td>
                        <td style="padding: 10px 0; font-weight: 500;">{empresa}</td>
                    </tr>
                </table>

                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 4px solid #ff9800; margin-bottom: 20px;">
                    <strong style="color: #333;">Por que é uma boa oportunidade:</strong><br>
                    <span style="color: #666;">{motivo}</span>
                </div>

                <a href="#" style="display: inline-block; background: #1a1a2e; color: white; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: bold;">
                    Ver Detalhes no Dashboard →
                </a>

                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    Encontrada em {datetime.now().strftime('%d/%m/%Y às %H:%M')} pelo ObraHunter
                </p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = destino
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email de alerta enviado para {destino}")
            return True
        except Exception as e:
            logger.error(f"Erro enviando email: {e}")
            return False

    async def enviar_webhook(
        self,
        url: str,
        obra_data: Dict,
        score: float,
        motivo: str,
    ) -> bool:
        """Envia alerta via webhook (Discord, Slack, Zapier, etc.)"""
        payload = {
            "text": f"🏗️ *Nova Oportunidade (Score {score}/10)*\n"
                    f"*{obra_data.get('titulo', '')}*\n"
                    f"📍 {obra_data.get('cidade', '')} - {obra_data.get('estado', '')}\n"
                    f"🏢 Tipo: {obra_data.get('tipo', '')}\n"
                    f"⚙️ Fase: {obra_data.get('fase', '')}\n"
                    f"🏭 Empresa: {obra_data.get('empresa_nome', 'N/A')}\n"
                    f"💡 {motivo}",
            "obra": obra_data,
            "score": score,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    success = resp.status < 300
                    if success:
                        logger.info(f"Webhook enviado para {url}")
                    return success
        except Exception as e:
            logger.error(f"Erro enviando webhook: {e}")
            return False

    async def enviar_push(
        self,
        destino: str,
        obra_data: Dict,
        score: float,
        motivo: str,
    ) -> bool:
        """Placeholder para push notifications (WebSocket/SSE no frontend)"""
        # Implementar com WebSocket no frontend
        logger.info(f"Push notification para {destino}: {obra_data.get('titulo')}")
        return True

    async def enviar_whatsapp(
        self,
        numero: str,
        obra_data: Dict,
        score: float,
        motivo: str,
    ) -> bool:
        """
        Envia via WhatsApp Business API (requer configuração).
        Alternativa: Twilio, Z-API, Evolution API.
        """
        logger.info(f"WhatsApp alerta para {numero} (não configurado)")
        return False

    async def enviar_alertas_obra(
        self,
        obra_data: Dict,
        score: float,
        motivo: str,
        configs_alerta: List[Dict],
    ) -> int:
        """Envia alertas por todos os canais configurados"""
        enviados = 0
        for config in configs_alerta:
            if config.get("ativo", True):
                success = await self.enviar_alerta(
                    tipo=config["tipo"],
                    destino=config["destino"],
                    obra_data=obra_data,
                    score=score,
                    motivo=motivo,
                )
                if success:
                    enviados += 1
        return enviados
