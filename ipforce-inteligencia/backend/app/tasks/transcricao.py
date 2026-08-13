import os
import tempfile
from celery import shared_task
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.chamada import Chamada
from app.models.transcricao import Transcricao
from app.services.pabx import pabx_service
from app.services.whisperx_service import whisperx_service

@shared_task(name="app.tasks.transcricao.processar_transcricao", max_retries=3, default_retry_delay=60)
def processar_transcricao(record_id: str):
    import asyncio
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_processar_transcricao(record_id))

async def _processar_transcricao(record_id: str):
    db = AsyncSessionLocal()
    try:
        result = await db.execute(select(Chamada).where(Chamada.record_id == record_id))
        chamada = result.scalar_one_or_none()
        if not chamada or chamada.transcrita:
            return {"status": "pulado", "motivo": "ja transcrita ou nao encontrada"}

        # Baixa gravacao
        audio_bytes = await pabx_service.baixar_gravacao(record_id, converter=1)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            resultado = whisperx_service.transcribe(tmp_path)

            transcricao = Transcricao(
                chamada_id=chamada.id,
                texto_completo=resultado["texto_completo"],
                segmentos=resultado["segmentos"],
                idioma=resultado["idioma"],
                tempo_processamento=resultado["tempo_processamento"],
            )
            db.add(transcricao)
            chamada.transcrita = True
            await db.commit()

            # Enfileira analise
            from app.tasks.analise import processar_analise
            processar_analise.delay(chamada.id)

            return {"status": "ok", "tempo": resultado["tempo_processamento"]}
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        await db.rollback()
        return {"status": "erro", "detail": str(e)}
    finally:
        await db.close()
