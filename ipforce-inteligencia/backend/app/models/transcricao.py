from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.models.base import Base

class Transcricao(Base):
    __tablename__ = "transcricoes"

    id = Column(Integer, primary_key=True, index=True)
    chamada_id = Column(Integer, ForeignKey("chamadas.id"), unique=True)
    texto_completo = Column(Text)
    segmentos = Column(JSON)  # lista de {inicio, fim, texto, speaker}
    idioma = Column(String)
    duracao_audio = Column(Float)
    tempo_processamento = Column(Float)
    erro = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
