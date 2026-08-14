import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.chamada import Chamada
from app.services.pabx import pabx_service

@shared_task(name="app.tasks.sync.sync_cdr_periodo")
def sync_cdr_periodo(data_inicial: str, data_final: str, hora_inicial: str = "00:00:00", hora_final: str = "23:59:59"):
    return asyncio.run(_sync_cdr_periodo(data_inicial, data_final, hora_inicial, hora_final))

async def _sync_cdr_periodo(data_inicial: str, data_final: str, hora_inicial: str = "00:00:00", hora_final: str = "23:59:59"):
    async with AsyncSessionLocal() as db:
        try:
            resultado = await pabx_service.get_cdr(data_inicial, data_final, formato="registros", hora_inicial=hora_inicial, hora_final=hora_final)
            if str(resultado.get("success")).lower() != "true":
                return {"status": "erro", "detail": resultado}
            registros = resultado.get("registros", []) or []
            novos_record_ids = []
            for reg in registros:
                record_id = reg.get("record")
                if not record_id:
                    continue
                existing = await db.execute(select(Chamada.id).where(Chamada.record_id == record_id))
                if existing.scalar_one_or_none() is not None:
                    continue
                try:
                    data_hora = datetime.strptime(reg.get("data_hora", ""), "%Y-%m-%d %H:%M:%S")
                except (TypeError, ValueError):
                    data_hora = datetime.now()
                db.add(Chamada(record_id=record_id, data_hora=data_hora, codigo=reg.get("codigo", ""), origem=reg.get("origem", ""), destino=reg.get("destino", ""), tronco=reg.get("tronco", ""), status=reg.get("status", ""), duracao=int(reg.get("duracao", 0) or 0), tarifa=reg.get("tarifa", ""), valor=reg.get("valor", ""), tipo=reg.get("tipo", ""), tem_gravacao=True))
                novos_record_ids.append(record_id)
            await db.commit()
            if novos_record_ids:
                from app.tasks.transcricao import processar_transcricao
                for record_id in novos_record_ids:
                    processar_transcricao.delay(record_id)
            return {"status": "ok", "criados": len(novos_record_ids), "total_api": len(registros)}
        except Exception as e:
            await db.rollback()
            return {"status": "erro", "detail": str(e)}

@shared_task(name="app.tasks.sync.sync_cdr_ultimos_30min")
def sync_cdr_ultimos_30min():
    agora = datetime.now()
    inicio = agora - timedelta(minutes=35)
    return sync_cdr_periodo(inicio.strftime("%Y-%m-%d"), agora.strftime("%Y-%m-%d"), inicio.strftime("%H:%M:%S"), agora.strftime("%H:%M:%S"))
