import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.chamada import Chamada
from app.services.pabx import pabx_service
from app.tasks.transcricao import processar_transcricao

@shared_task(name="app.tasks.sync.sync_cdr_periodo")
def sync_cdr_periodo(data_inicial: str, data_final: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_sync_cdr_periodo(data_inicial, data_final))

async def _sync_cdr_periodo(data_inicial: str, data_final: str):
    db = AsyncSessionLocal()
    try:
        resultado = await pabx_service.get_cdr(data_inicial, data_final, formato="registros")
        if resultado.get("success") != "true":
            return {"status": "erro", "detail": resultado}

        registros = resultado.get("registros", [])
        criados = 0

        for reg in registros:
            record_id = reg.get("record")
            if not record_id:
                continue

            existing = await db.execute(select(Chamada).where(Chamada.record_id == record_id))
            if existing.scalar_one_or_none():
                continue

            data_hora_str = reg.get("data_hora", "")
            try:
                data_hora = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M:%S")
            except:
                data_hora = datetime.now()

            chamada = Chamada(
                record_id=record_id,
                data_hora=data_hora,
                codigo=reg.get("codigo", ""),
                origem=reg.get("origem", ""),
                destino=reg.get("destino", ""),
                tronco=reg.get("tronco", ""),
                status=reg.get("status", ""),
                duracao=int(reg.get("duracao", 0) or 0),
                tarifa=reg.get("tarifa", ""),
                valor=reg.get("valor", ""),
                tipo=reg.get("tipo", ""),
                tem_gravacao=bool(record_id),
            )
            db.add(chamada)
            criados += 1

        await db.commit()

        # Enfileira transcricoes para chamadas novas com gravacao
        for reg in registros:
            record_id = reg.get("record")
            if record_id:
                processar_transcricao.delay(record_id)

        return {"status": "ok", "criados": criados, "total_api": len(registros)}
    except Exception as e:
        await db.rollback()
        return {"status": "erro", "detail": str(e)}
    finally:
        await db.close()

@shared_task(name="app.tasks.sync.sync_cdr_ultimos_30min")
def sync_cdr_ultimos_30min():
    agora = datetime.now()
    inicio = (agora - timedelta(minutes=35)).strftime("%Y-%m-%d")
    fim = agora.strftime("%Y-%m-%d")
    return sync_cdr_periodo(inicio, fim)
