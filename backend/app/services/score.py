"""
ObraHunter - Serviço de Score de Oportunidade
Calcula score de 0-10 para cada obra, determinando prioridade de prospecção
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ScoreService:
    """
    Calcula o score de oportunidade de cada obra.
    Score de 0 a 10 — quanto maior, melhor a oportunidade.
    """

    # Pesos configuráveis
    PESO_PORTE = settings.SCORE_PESO_PORTE          # 0.30
    PESO_FASE = settings.SCORE_PESO_FASE             # 0.25
    PESO_TIPO = settings.SCORE_PESO_TIPO             # 0.20
    PESO_CONTATOS = settings.SCORE_PESO_CONTATOS     # 0.15
    PESO_RECENCIA = settings.SCORE_PESO_RECENCIA     # 0.10

    # Scores por porte
    SCORE_PORTE = {
        "grande": 10,
        "medio": 7,
        "pequeno": 4,
        "desconhecido": 5,
    }

    # Scores por fase (momento ideal para prospectar)
    SCORE_FASE = {
        "aprovacao": 9,      # Melhor momento - início do projeto
        "fundacao": 10,      # Muito bom - obra começando
        "estrutura": 7,      # Bom - ainda comprando material
        "acabamento": 5,     # OK - final da obra
        "entrega": 2,        # Ruim - obra acabando
        "desconhecida": 5,   # Neutro
    }

    # Scores por tipo de obra
    SCORE_TIPO = {
        "comercial": 9,
        "industrial": 9,
        "residencial": 7,
        "institucional": 8,
        "infraestrutura": 8,
        "loteamento": 7,
        "reforma": 5,
        "misto": 7,
        "desconhecido": 5,
    }

    def calcular_score(self, obra_data: Dict[str, Any]) -> float:
        """
        Calcula score final de uma obra (0-10).

        Fatores:
        - Porte (30%): Obras maiores = mais oportunidade
        - Fase (25%): Fases iniciais = melhor timing
        - Tipo (20%): Comercial/industrial = maior ticket médio
        - Contatos (15%): Mais dados de contato = mais fácil prospectar
        - Recência (10%): Obra mais recente = mais urgente
        """
        score_porte = self._score_porte(obra_data)
        score_fase = self._score_fase(obra_data)
        score_tipo = self._score_tipo(obra_data)
        score_contatos = self._score_contatos(obra_data)
        score_recencia = self._score_recencia(obra_data)

        score_final = (
            score_porte * self.PESO_PORTE +
            score_fase * self.PESO_FASE +
            score_tipo * self.PESO_TIPO +
            score_contatos * self.PESO_CONTATOS +
            score_recencia * self.PESO_RECENCIA
        )

        # Bônus por valor estimado alto
        valor = obra_data.get("valor_estimado")
        if valor:
            if valor > 10_000_000:
                score_final = min(10, score_final + 1.5)
            elif valor > 5_000_000:
                score_final = min(10, score_final + 1.0)
            elif valor > 1_000_000:
                score_final = min(10, score_final + 0.5)

        # Bônus por área grande
        area = obra_data.get("area_m2")
        if area:
            if area > 10000:
                score_final = min(10, score_final + 1.0)
            elif area > 5000:
                score_final = min(10, score_final + 0.5)

        return round(min(10, max(0, score_final)), 2)

    def _score_porte(self, data: Dict) -> float:
        porte = data.get("porte", "desconhecido")
        return self.SCORE_PORTE.get(porte, 5)

    def _score_fase(self, data: Dict) -> float:
        fase = data.get("fase", "desconhecida")
        return self.SCORE_FASE.get(fase, 5)

    def _score_tipo(self, data: Dict) -> float:
        tipo = data.get("tipo", "desconhecido")
        return self.SCORE_TIPO.get(tipo, 5)

    def _score_contatos(self, data: Dict) -> float:
        """Quanto mais dados de contato, melhor"""
        score = 0
        if data.get("empresa_cnpj"):
            score += 3
        if data.get("empresa_site"):
            score += 2
        if data.get("empresa_nome"):
            score += 2
        if data.get("tem_email"):
            score += 2
        if data.get("tem_telefone"):
            score += 1
        return min(10, score)

    def _score_recencia(self, data: Dict) -> float:
        """Obras mais recentes = score maior"""
        data_encontrada = data.get("data_encontrada")
        if not data_encontrada:
            return 5

        if isinstance(data_encontrada, str):
            data_encontrada = datetime.fromisoformat(data_encontrada)

        dias = (datetime.utcnow() - data_encontrada).days

        if dias <= 1:
            return 10
        elif dias <= 3:
            return 9
        elif dias <= 7:
            return 8
        elif dias <= 14:
            return 6
        elif dias <= 30:
            return 4
        elif dias <= 90:
            return 2
        return 1

    def classificar_oportunidade(self, score: float) -> str:
        """Classifica a oportunidade pelo score"""
        if score >= 8.5:
            return "🔥 Quente"
        elif score >= 7.0:
            return "⭐ Muito Boa"
        elif score >= 5.0:
            return "👍 Boa"
        elif score >= 3.0:
            return "😐 Regular"
        return "❄️ Fria"

    def deve_alertar(self, score: float) -> bool:
        """Verifica se a obra deve gerar alerta"""
        return score >= settings.SCORE_THRESHOLD_ALERTA

    def gerar_motivo_alerta(self, obra_data: Dict, score: float) -> str:
        """Gera texto explicando por que a obra é uma boa oportunidade"""
        motivos = []

        porte = obra_data.get("porte", "")
        if porte == "grande":
            motivos.append("Obra de grande porte")
        
        fase = obra_data.get("fase", "")
        if fase in ["aprovacao", "fundacao"]:
            motivos.append("Fase inicial — timing ideal para contato")

        tipo = obra_data.get("tipo", "")
        if tipo in ["comercial", "industrial"]:
            motivos.append(f"Obra {tipo} — ticket médio alto")

        valor = obra_data.get("valor_estimado")
        if valor and valor > 5_000_000:
            motivos.append(f"Valor estimado: R$ {valor:,.0f}")

        area = obra_data.get("area_m2")
        if area and area > 5000:
            motivos.append(f"Área: {area:,.0f} m²")

        if not motivos:
            motivos.append(f"Score de oportunidade: {score}/10")

        return " | ".join(motivos)
