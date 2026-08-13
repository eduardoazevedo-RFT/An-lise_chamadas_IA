from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.chamada import Chamada
from app.models.transcricao import Transcricao
from app.models.analise import Analise

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/hoje")
async def dashboard_hoje(db: AsyncSession = Depends(get_db)):
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    amanha = hoje + timedelta(days=1)

    total = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha))
    atendidas = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.status == "ATENDIDA"))
    nao_atendidas = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.status != "ATENDIDA"))
    transcritas = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.transcrita == True))
    analisadas = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.analisada == True))
    alertas = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.alerta_nivel.in_(["importante", "critico"])))
    oportunidades = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.oportunidade == True))

    duracao = await db.execute(select(func.sum(Chamada.duracao)).where(Chamada.data_hora >= hoje, Chamada.data_hora < amanha, Chamada.status == "ATENDIDA"))
    duracao_total = duracao.scalar() or 0

    return {
        "data": hoje.strftime("%Y-%m-%d"),
        "total_ligacoes": total.scalar(),
        "atendidas": atendidas.scalar(),
        "nao_atendidas": nao_atendidas.scalar(),
        "duracao_total_segundos": duracao_total,
        "transcritas": transcritas.scalar(),
        "analisadas": analisadas.scalar(),
        "alertas": alertas.scalar(),
        "oportunidades": oportunidades.scalar(),
    }

@router.get("/alertas")
async def listar_alertas(db: AsyncSession = Depends(get_db), limit: int = 20):
    result = await db.execute(
        select(Chamada)
        .where(Chamada.alerta_nivel.in_(["importante", "critico"]))
        .order_by(Chamada.data_hora.desc())
        .limit(limit)
    )
    chamadas = result.scalars().all()
    return {
        "items": [
            {
                "id": c.id,
                "record_id": c.record_id,
                "data_hora": c.data_hora.isoformat() if c.data_hora else None,
                "origem": c.origem,
                "destino": c.destino,
                "status": c.status,
                "alerta_nivel": c.alerta_nivel,
                "oportunidade": c.oportunidade,
            }
            for c in chamadas
        ]
    }
