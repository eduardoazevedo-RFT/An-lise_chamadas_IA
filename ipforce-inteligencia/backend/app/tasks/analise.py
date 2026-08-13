import asyncio
import json
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.chamada import Chamada
from app.models.transcricao import Transcricao
from app.models.analise import Analise
from app.services.ollama_service import ollama_service

@shared_task(name="app.tasks.analise.processar_analise", max_retries=2, default_retry_delay=30)
def processar_analise(chamada_id: int):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_processar_analise(chamada_id))

async def _processar_analise(chamada_id: int):
    db = AsyncSessionLocal()
    try:
        result = await db.execute(select(Chamada).where(Chamada.id == chamada_id))
        chamada = result.scalar_one_or_none()
        if not chamada or chamada.analisada:
            return {"status": "pulado"}

        t = await db.execute(select(Transcricao).where(Transcricao.chamada_id == chamada_id))
        transcricao = t.scalar_one_or_none()
        if not transcricao:
            return {"status": "erro", "motivo": "sem transcricao"}

        resultado = await ollama_service.analisar_chamada(transcricao.texto_completo)

        analise = Analise(
            chamada_id=chamada_id,
            resumo=resultado.get("resumo", ""),
            motivo_contato=resultado.get("motivo_contato", ""),
            solicitacoes_cliente=resultado.get("solicitacoes_cliente", []),
            acoes_atendente=resultado.get("acoes_atendente", []),
            acoes_prometidas=resultado.get("acoes_prometidas", []),
            pendencias=resultado.get("pendencias", []),
            duvidas_nao_respondidas=resultado.get("duvidas_nao_respondidas", []),
            objecoes=resultado.get("objecoes", []),
            reclamacoes=resultado.get("reclamacoes", []),
            indicio_insatisfacao=resultado.get("indicio_insatisfacao", False),
            falhas_comunicacao=resultado.get("falhas_comunicacao", []),
            oportunidades=resultado.get("oportunidades", []),
            proximos_passos=resultado.get("proximos_passos", []),
            sugestoes_melhoria=resultado.get("sugestoes_melhoria", []),
            alerta_nivel=resultado.get("alerta_nivel", "informacao"),
            alerta_evidencias=resultado.get("alerta_evidencias", []),
            oportunidade_evidencias=resultado.get("oportunidade_evidencias", []),
            tempo_processamento=resultado.get("tempo_processamento", 0),
            erro=resultado.get("erro"),
        )
        db.add(analise)

        chamada.analisada = True
        chamada.alerta_nivel = analise.alerta_nivel
        chamada.oportunidade = len(analise.oportunidades) > 0

        await db.commit()
        return {"status": "ok", "alerta_nivel": analise.alerta_nivel}
    except Exception as e:
        await db.rollback()
        return {"status": "erro", "detail": str(e)}
    finally:
        await db.close()

@shared_task(name="app.tasks.analise.gerar_resumo_diario")
def gerar_resumo_diario():
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_gerar_resumo_diario())

async def _gerar_resumo_diario():
    db = AsyncSessionLocal()
    try:
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Aqui voce pode gerar um resumo consolidado via Ollama
        # Por enquanto, retorna indicadores
        from sqlalchemy import func
        total = await db.execute(select(func.count()).where(Chamada.data_hora >= hoje))
        return {"status": "ok", "total_hoje": total.scalar()}
    finally:
        await db.close()
