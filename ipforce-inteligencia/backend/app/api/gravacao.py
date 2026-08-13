from fastapi import APIRouter, HTTPException, Response
from app.services.pabx import pabx_service
import httpx

router = APIRouter(prefix="/gravacao", tags=["gravacao"])

@router.get("/{record_id}")
async def proxy_gravacao(record_id: str, converter: int = 1):
    url = pabx_service.get_gravacao_url(record_id, converter)
    try:
        async with httpx.AsyncClient(verify=False, timeout=120) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "audio/mpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"Content-Disposition": f"inline; filename={record_id}.mp3"},
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Erro ao obter gravacao do PABX")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
