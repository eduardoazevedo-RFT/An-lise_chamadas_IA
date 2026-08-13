import httpx
import json
import time
from typing import Dict, Any, List
from app.core.config import settings

class OllamaService:
    def __init__(self):
        self.host = settings.OLLAMA_HOST.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    async def generate(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 2048},
        }
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 2048},
        }
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def analisar_chamada(self, transcricao: str) -> Dict[str, Any]:
        system = """Voce e um analista de qualidade de atendimento telefonico.
Analise a transcricao da conversa entre atendente e cliente.
Responda APENAS em JSON valido, sem markdown, sem explicacoes fora do JSON.
"""
        prompt = f"""Transcricao da chamada:
{transcricao}

Analise e retorne um JSON com estas chaves:
- resumo: resumo de ate 3 frases
- motivo_contato: tema principal
- solicitacoes_cliente: array de strings
- acoes_atendente: array de strings
- acoes_prometidas: array de strings
- pendencias: array de strings
- duvidas_nao_respondidas: array de strings
- objecoes: array de strings
- reclamacoes: array de strings
- indicio_insatisfacao: true ou false
- falhas_comunicacao: array de strings
- oportunidades: array de objetos {{"descricao": "...", "evidencia": "..."}}
- proximos_passos: array de strings
- sugestoes_melhoria: array de strings
- alerta_nivel: "informacao", "atencao", "importante" ou "critico"
- alerta_evidencias: array de objetos {{"motivo": "...", "trecho": "..."}}
- oportunidade_evidencias: array de objetos {{"descricao": "...", "trecho": "..."}}
"""
        start = time.time()
        try:
            raw = await self.chat([
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ])
            # Tenta extrair JSON
            raw = raw.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            resultado = json.loads(raw)
            resultado["tempo_processamento"] = time.time() - start
            resultado["erro"] = None
            return resultado
        except Exception as e:
            return {
                "resumo": "Erro na analise.",
                "motivo_contato": "",
                "solicitacoes_cliente": [],
                "acoes_atendente": [],
                "acoes_prometidas": [],
                "pendencias": [],
                "duvidas_nao_respondidas": [],
                "objecoes": [],
                "reclamacoes": [],
                "indicio_insatisfacao": False,
                "falhas_comunicacao": [],
                "oportunidades": [],
                "proximos_passos": [],
                "sugestoes_melhoria": [],
                "alerta_nivel": "informacao",
                "alerta_evidencias": [],
                "oportunidade_evidencias": [],
                "tempo_processamento": time.time() - start,
                "erro": str(e),
            }

ollama_service = OllamaService()
