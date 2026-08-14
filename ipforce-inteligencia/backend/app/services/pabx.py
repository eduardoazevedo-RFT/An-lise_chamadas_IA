import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings

class PABXService:
    def __init__(self):
        self.base_url = settings.PABX_BASE_URL.rstrip("/")
        self.api_key = settings.PABX_API_KEY

    async def get_cdr(
        self,
        data_inicial: str,
        data_final: str,
        formato: str = "registros",
        origem: Optional[str] = None,
        destino: Optional[str] = None,
        hora_inicial: str = "00:00:00",
        hora_final: str = "23:59:59",
    ) -> Dict[str, Any]:
        if not self.base_url or not self.api_key:
            raise RuntimeError("PABX_BASE_URL e PABX_API_KEY precisam estar configurados no .env")
        url = f"{self.base_url}/api/cdr"
        data = {
            "formato": formato,
            "data_inicial": data_inicial,
            "data_final": data_final,
            "hora_inicial": hora_inicial,
            "hora_final": hora_final,
        }
        if origem:
            data["origem"] = origem
        if destino:
            data["destino"] = destino

        async with httpx.AsyncClient(verify=False, timeout=60) as client:
            resp = await client.post(url, data=data, auth=(self.api_key, ""))
            resp.raise_for_status()
            return resp.json()

    def get_gravacao_url(self, record_id: str, converter: int = 1) -> str:
        if not self.base_url or not self.api_key:
            raise RuntimeError("PABX_BASE_URL e PABX_API_KEY precisam estar configurados no .env")
        return f"{self.base_url}/api/recordticket/{self.api_key}/{record_id}/{converter}"

    async def baixar_gravacao(self, record_id: str, converter: int = 1) -> bytes:
        url = self.get_gravacao_url(record_id, converter)
        async with httpx.AsyncClient(verify=False, timeout=120) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content

pabx_service = PABXService()
