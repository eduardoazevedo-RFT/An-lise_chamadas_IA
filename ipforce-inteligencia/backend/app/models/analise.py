from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.sql import func
from app.models.base import Base

class Analise(Base):
    __tablename__ = "analises"

    id = Column(Integer, primary_key=True, index=True)
    chamada_id = Column(Integer, ForeignKey("chamadas.id"), unique=True)
    resumo = Column(Text)
    motivo_contato = Column(String)
    solicitacoes_cliente = Column(JSON)
    acoes_atendente = Column(JSON)
    acoes_prometidas = Column(JSON)
    pendencias = Column(JSON)
    duvidas_nao_respondidas = Column(JSON)
    objecoes = Column(JSON)
    reclamacoes = Column(JSON)
    indicio_insatisfacao = Column(Boolean, default=False)
    falhas_comunicacao = Column(JSON)
    oportunidades = Column(JSON)
    proximos_passos = Column(JSON)
    sugestoes_melhoria = Column(JSON)
    alerta_nivel = Column(String, default="informacao")
    alerta_evidencias = Column(JSON)  # trechos da transcricao que justificam
    oportunidade_evidencias = Column(JSON)
    tempo_processamento = Column(Float)
    erro = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
