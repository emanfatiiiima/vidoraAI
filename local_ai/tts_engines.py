"""
Local text-to-speech engines. Each ``synthesize_*`` returns WAV bytes.

``speed`` is a multiplier (1.0 = normal, 1.2 = 20% faster).
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from local_ai.catalog import ENGINES, PIPER_VOICE_FILES
from local_ai.runtime import MELO_PYTHON, PACKAGE_DIR, SLOT, EngineInputError, EngineNotReady, cuda_device

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def synthesize(engine: str, text: str, voice: str | None, speed: float) -> bytes:
    text = " ".join(text.split())
    if not text:
        raise EngineInputError("Text is required.")
    voice = voice or ENGINES[engine].voices[0].id
    return _SYNTHESIZERS[engine](text, voice, speed)


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def to_wav(samples: np.ndarray, sample_rate: int) -> bytes:
    """Float samples in [-1, 1] -> 16-bit mono WAV bytes."""
    pcm = (np.clip(np.asarray(samples, dtype=np.float32).reshape(-1), -1.0, 1.0) * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return buffer.getvalue()


def chunk_sentences(text: str, max_chars: int) -> list[str]:
    """Group sentences into chunks no longer than ``max_chars`` (long sentences are cut on commas/spaces)."""
    chunks: list[str] = []
    current = ""
    for sentence in _SENTENCE_RE.split(text):
        while len(sentence) > max_chars:
            cut = max(sentence.rfind(", ", 0, max_chars), sentence.rfind(" ", 0, max_chars))
            cut = cut if cut > 0 else max_chars
            chunks.append(sentence[:cut].strip(" ,"))
            sentence = sentence[cut:].strip(" ,")
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return [c for c in chunks if c]


# ---------------------------------------------------------------------- #
# Kokoro
# ---------------------------------------------------------------------- #
def _load_kokoro():
    from kokoro import KPipeline

    device = cuda_device()
    # One pipeline per accent: "a" = American English, "b" = British English.
    return {lang: KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M", device=device) for lang in ("a", "b")}


def _kokoro(text: str, voice: str, speed: float) -> bytes:
    with SLOT.use("kokoro", _load_kokoro) as pipelines:
        pipeline = pipelines["b" if voice.startswith("b") else "a"]
        parts = [np.asarray(audio, dtype=np.float32) for _, _, audio in pipeline(text, voice=voice, speed=speed)]
    if not parts:
        raise EngineInputError("Kokoro produced no audio for this text.")
    return to_wav(np.concatenate(parts), 24_000)


# ---------------------------------------------------------------------- #
# Piper (CPU)
# ---------------------------------------------------------------------- #
def _piper(text: str, voice: str, speed: float) -> bytes:
    from huggingface_hub import hf_hub_download
    from piper import PiperVoice, SynthesisConfig

    if voice not in PIPER_VOICE_FILES:
        raise EngineInputError(f"Unknown Piper voice '{voice}'.")
    path = PIPER_VOICE_FILES[voice]
    try:
        # The .onnx.json config must sit next to the model - both come from the same snapshot.
        hf_hub_download("rhasspy/piper-voices", f"{path}.onnx.json", local_files_only=True)
        model = hf_hub_download("rhasspy/piper-voices", f"{path}.onnx", local_files_only=True)
    except Exception as exc:  # noqa: BLE001
        raise EngineNotReady("Piper voices are not downloaded. Run: python -m local_ai.download piper") from exc

    piper_voice = PiperVoice.load(model)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        # length_scale > 1 is slower speech.
        piper_voice.synthesize_wav(text, wav, syn_config=SynthesisConfig(length_scale=1.0 / speed))
    return buffer.getvalue()


# ---------------------------------------------------------------------- #
# Coqui XTTS-v2
# ---------------------------------------------------------------------- #
XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def _load_xtts():
    if os.environ.get("COQUI_TOS_AGREED") != "1":
        raise EngineNotReady(
            "XTTS-v2 is under the Coqui Public Model License. Read it "
            "(https://coqui.ai/cpml), then set COQUI_TOS_AGREED=1 for the worker."
        )
    from TTS.api import TTS

    return TTS(XTTS_MODEL).to(cuda_device())


def _xtts(text: str, voice: str, speed: float) -> bytes:
    with SLOT.use("xtts", _load_xtts) as tts:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "speech.wav"
            tts.tts_to_file(text=text, speaker=voice, language="en", file_path=str(out),
                            speed=speed, split_sentences=True)
            return out.read_bytes()


# ---------------------------------------------------------------------- #
# MeloTTS (separate venv, run as a subprocess)
# ---------------------------------------------------------------------- #
def _melo(text: str, voice: str, speed: float) -> bytes:
    if not MELO_PYTHON.is_file():
        raise EngineNotReady(f"MeloTTS venv not found at {MELO_PYTHON}. See LOCAL_SETUP.md, step 6.")
    # Melo runs in its own process, so free the GPU slot for it.
    SLOT.unload()
    with tempfile.TemporaryDirectory() as tmp:
        text_file, out = Path(tmp) / "text.txt", Path(tmp) / "speech.wav"
        text_file.write_text(text, encoding="utf-8")
        result = subprocess.run(
            [str(MELO_PYTHON), str(PACKAGE_DIR / "melo_cli.py"), "--text-file", str(text_file),
             "--out", str(out), "--speaker", voice, "--speed", f"{speed:.2f}"],
            capture_output=True, text=True, timeout=1800,
        )
        if result.returncode != 0 or not out.is_file():
            tail = (result.stderr or result.stdout).strip().splitlines()[-5:]
            raise RuntimeError("MeloTTS failed: " + " | ".join(tail))
        return out.read_bytes()


# ---------------------------------------------------------------------- #
# Bark (via transformers)
# ---------------------------------------------------------------------- #
BARK_REPO = "suno/bark-small"
# Bark generates at most ~13 s per call, so the script is fed in short chunks.
BARK_MAX_CHARS = 180


def _load_bark():
    import torch
    from transformers import AutoProcessor, BarkModel

    device = cuda_device()
    model = BarkModel.from_pretrained(BARK_REPO, torch_dtype=torch.float16).to(device)
    return AutoProcessor.from_pretrained(BARK_REPO), model


def _to_device(value, device):
    if hasattr(value, "to"):
        return value.to(device)
    if isinstance(value, dict):
        return {k: _to_device(v, device) for k, v in value.items()}
    return value


def _bark(text: str, voice: str, speed: float) -> bytes:
    import torch

    with SLOT.use("bark", _load_bark) as (processor, model):
        rate = model.generation_config.sample_rate
        pause = np.zeros(int(rate * 0.2), dtype=np.float32)
        parts: list[np.ndarray] = []
        for chunk in chunk_sentences(text, BARK_MAX_CHARS):
            inputs = processor(chunk, voice_preset=voice)
            inputs = {k: _to_device(v, model.device) for k, v in inputs.items()}
            with torch.inference_mode():
                audio = model.generate(**inputs)
            parts += [audio.float().cpu().numpy().reshape(-1), pause]
    return to_wav(np.concatenate(parts), rate)


_SYNTHESIZERS = {"kokoro": _kokoro, "piper": _piper, "xtts": _xtts, "melo": _melo, "bark": _bark}
