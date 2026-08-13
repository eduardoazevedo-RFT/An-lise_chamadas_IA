from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from datetime import datetime, date
from app.core.database import get_db
from app.api.auth import oauth2_scheme, decode_token
from app.models.chamada import Chamada
from app.models.transcricao import Transcricao
from app.models.analise import Analise
from app.services.pabx import pabx_service
from app.tasks.sync import sync_cdr_periodo

router = APIRouter(prefix="/cdr", tags=["cdr"])

@router.get("/")
async def listar_cdr(
    db: AsyncSession = Depends(get_db),
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    origem: Optional[str] = None,
    destino: Optional[str] = None,
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    tem_gravacao: Optional[bool] = None,
    transcrita: Optional[bool] = None,
    alerta_nivel: Optional[str] = None,
    oportunidade: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    query = select(Chamada)

    if data_inicio:
        query = query.where(Chamada.data_hora >= datetime.combine(data_inicio, datetime.min.time()))
    if data_fim:
        query = query.where(Chamada.data_hora <= datetime.combine(data_fim, datetime.max.time()))
    if origem:
        query = query.where(Chamada.origem.ilike(f"%{origem}%"))
    if destino:
        query = query.where(Chamada.destino.ilike(f"%{destino}%"))
    if status:
        query = query.where(Chamada.status == status)
    if tipo:
        query = query.where(Chamada.tipo == tipo)
    if tem_gravacao is not None:
        query = query.where(Chamada.tem_gravacao == tem_gravacao)
    if transcrita is not None:
        query = query.where(Chamada.transcrita == transcrita)
    if alerta_nivel:
        query = query.where(Chamada.alerta_nivel == alerta_nivel)
    if oportunidade is not None:
        query = query.where(Chamada.oportunidade == oportunidade)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(Chamada.data_hora.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    chamadas = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": c.id,
                "record_id": c.record_id,
                "data_hora": c.data_hora.isoformat() if c.data_hora else None,
                "origem": c.origem,
                "destino": c.destino,
                "status": c.status,
                "duracao": c.duracao,
                "tipo": c.tipo,
                "tem_gravacao": c.tem_gravacao,
                "transcrita": c.transcrita,
                "analisada": c.analisada,
                "alerta_nivel": c.alerta_nivel,
                "oportunidade": c.oportunidade,
            }
            for c in chamadas
        ],
    }

@router.get("/{chamada_id}")
async def detalhe_chamada(chamada_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chamada).where(Chamada.id == chamada_id))
    chamada = result.scalar_one_or_none()
    if not chamada:
        raise HTTPException(status_code=404, detail="Chamada nao encontrada")

    transcricao = None
    analise = None

    if chamada.transcrita:
        t = await db.execute(select(Transcricao).where(Transcricao.chamada_id == chamada_id))
        transcricao = t.scalar_one_or_none()

    if chamada.analisada:
        a = await db.execute(select(Analise).where(Analise.chamada_id == chamada_id))
        analise = a.scalar_one_or_none()

    return {
        "chamada": {
            "id": chamada.id,
            "record_id": chamada.record_id,
            "data_hora": chamada.data_hora.isoformat() if chamada.data_hora else None,
            "codigo": chamada.codigo,
            "origem": chamada.origem,
            "destino": chamada.destino,
            "tronco": chamada.tronco,
            "status": chamada.status,
            "duracao": chamada.duracao,
            "duracao_atendimento": chamada.duracao_atendimento,
            "tarifa": chamada.tarifa,
            "valor": chamada.valor,
            "tipo": chamada.tipo,
            "tem_gravacao": chamada.tem_gravacao,
            "transcrita": chamada.transcrita,
            "analisada": chamada.analisada,
            "alerta_nivel": chamada.alerta_nivel,
            "oportunidade": chamada.oportunidade,
        },
        "transcricao": {
            "texto_completo": transcricao.texto_completo,
            "segmentos": transcricao.segmentos,
            "idioma": transcricao.idioma,
            "tempo_processamento": transcricao.tempo_processamento,
        } if transcricao else None,
        "analise": {
            "resumo": analise.resumo,
            "motivo_contato": analise.motivo_contato,
            "solicitacoes_cliente": analise.solicitacoes_cliente,
            "acoes_atendente": analise.acoes_atendente,
            "acoes_prometidas": analise.acoes_prometidas,
            "pendencias": analise.pendencias,
            "duvidas_nao_respondidas": analise.duvidas_nao_respondidas,
            "objecoes": analise.objecoes,
            "reclamacoes": analise.reclamacoes,
            "indicio_insatisfacao": analise.indicio_insatisfacao,
            "falhas_comunicacao": analise.falhas_comunicacao,
            "oportunidades": analise.oportunidades,
            "proximos_passos": analise.proximos_passos,
            "sugestoes_melhoria": analise.sugestoes_melhoria,
            "alerta_nivel": analise.alerta_nivel,
            "alerta_evidencias": analise.alerta_evidencias,
            "oportunidade_evidencias": analise.oportunidade_evidencias,
        } if analise else None,
    }

@router.post("/sync")
async def forcar_sync(data_inicial: str, data_final: str):
    task = sync_cdr_periodo.delay(data_inicial, data_final)
    return {"task_id": task.id, "status": "iniciado"}
