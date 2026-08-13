import os
import time
import tempfile
import whisperx
import torch
from app.core.config import settings

class WhisperXService:
    def __init__(self):
        self.device = settings.WHISPER_DEVICE if torch.cuda.is_available() else "cpu"
        self.compute_type = settings.WHISPER_COMPUTE_TYPE if torch.cuda.is_available() else "int8"
        self.model_name = settings.WHISPER_MODEL
        self.model = None
        self.align_model = None
        self.diarize_model = None
        self._load_model()

    def _load_model(self):
        print(f"[WhisperX] Carregando modelo {self.model_name} em {self.device}...")
        self.model = whisperx.load_model(
            self.model_name,
            self.device,
            compute_type=self.compute_type,
            language="pt",
        )
        print("[WhisperX] Modelo carregado.")

    def transcribe(self, audio_path: str) -> dict:
        start = time.time()

        # 1. Transcricao
        result = self.model.transcribe(audio_path, batch_size=16)

        # 2. Alinhamento de palavras
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
        result = whisperx.align(result["segments"], model_a, metadata, audio_path, self.device)

        # 3. Diarizacao (opcional)
        if settings.HF_TOKEN:
            try:
                diarize_model = whisperx.DiarizationPipeline(
                    model_name="pyannote/speaker-diarization-3.1",
                    use_auth_token=settings.HF_TOKEN,
                    device=self.device,
                )
                diarize_segments = diarize_model(audio_path)
                result = whisperx.assign_word_speakers(diarize_segments, result)
            except Exception as e:
                print(f"[WhisperX] Diarizacao falhou: {e}")

        elapsed = time.time() - start

        texto = " ".join([s["text"] for s in result["segments"]])
        segmentos = []
        for s in result["segments"]:
            seg = {
                "inicio": s.get("start", 0),
                "fim": s.get("end", 0),
                "texto": s.get("text", "").strip(),
                "speaker": s.get("speaker", "SPEAKER_X"),
            }
            segmentos.append(seg)

        return {
            "texto_completo": texto,
            "segmentos": segmentos,
            "idioma": result.get("language", "pt"),
            "tempo_processamento": elapsed,
        }

whisperx_service = WhisperXService()
