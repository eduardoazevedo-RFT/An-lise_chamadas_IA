from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class Chamada(Base):
    __tablename__ = "chamadas"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String, index=True, unique=True)  # campo record do CDR
    data_hora = Column(DateTime(timezone=True), index=True)
    codigo = Column(String)
    origem = Column(String, index=True)
    destino = Column(String, index=True)
    tronco = Column(String)
    status = Column(String, index=True)
    duracao = Column(Integer)
    duracao_atendimento = Column(Integer, default=0)
    tarifa = Column(String)
    valor = Column(String)
    tipo = Column(String, index=True)
    tem_gravacao = Column(Boolean, default=False)
    gravacao_baixada = Column(Boolean, default=False)
    transcrita = Column(Boolean, default=False)
    analisada = Column(Boolean, default=False)
    alerta_nivel = Column(String, default="informacao")  # informacao, atencao, importante, critico
    oportunidade = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
