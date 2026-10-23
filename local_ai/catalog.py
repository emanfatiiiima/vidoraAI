"""
Catalog of every local model VidoraAI can use (single source of truth).

This module is pure data with no third-party imports, so it is shared by both
sides of the local setup:

* the **GPU worker** (``local_ai.server``, its own venv with PyTorch) uses it to
  know what to download and how to run each engine;
* the **main backend** (``core``) uses it to label the options in the
  "Choose your AIs" popup and list the voices of each TTS engine.

Text generation is not listed here: it runs in Ollama, and every model you
``ollama pull`` shows up in the popup automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Voice:
    id: str
    name: str
    desc: str
    type: str  # "Female" | "Male"


@dataclass(frozen=True, slots=True)
class Download:
    """One Hugging Face download needed by an engine."""

    repo: str
    #: Only these files are fetched (repos often also hold huge single-file checkpoints).
    allow: tuple[str, ...] | None = None
    #: Download a single file instead of a snapshot.
    filename: str | None = None


@dataclass(frozen=True, slots=True)
class Engine:
    id: str
    kind: str  # "tts" | "image" | "video"
    label: str
    #: Python modules that must be importable in the worker venv.
    modules: tuple[str, ...]
    downloads: tuple[Download, ...] = ()
    #: Rough size of the download, shown by ``python -m local_ai.download --list``.
    size: str = ""
    note: str = ""
    voices: tuple[Voice, ...] = field(default_factory=tuple)


# Patterns for diffusers repos that ship fp16 variants next to fp32 weights.
_FP16 = ("*.json", "*.txt", "*.model", "*/*fp16.safetensors")
# Diffusers repos whose weights are already half precision (no variant files).
_SUBFOLDER_WEIGHTS = ("*.json", "*.txt", "*.model", "*/*.safetensors")

# ---------------------------------------------------------------------- #
# Text to speech
# ---------------------------------------------------------------------- #
#: Piper voice id -> path inside the ``rhasspy/piper-voices`` repo (without extension).
PIPER_VOICE_FILES: dict[str, str] = {
    "en_US-lessac-medium": "en/en_US/lessac/medium/en_US-lessac-medium",
    "en_US-ryan-high": "en/en_US/ryan/high/en_US-ryan-high",
    "en_US-amy-medium": "en/en_US/amy/medium/en_US-amy-medium",
    "en_GB-alan-medium": "en/en_GB/alan/medium/en_GB-alan-medium",
}

TTS_ENGINES: tuple[Engine, ...] = (
    Engine(
        id="kokoro",
        kind="tts",
        label="Kokoro TTS",
        modules=("kokoro", "soundfile"),
        downloads=(Download("hexgrad/Kokoro-82M", allow=("config.json", "kokoro-v1_0.pth", "voices/*")),),
        size="0.4 GB",
        note="Best quality-for-speed. Recommended default.",
        voices=(
            Voice("af_heart", "Heart", "Warm & natural", "Female"),
            Voice("af_bella", "Bella", "Expressive & bright", "Female"),
            Voice("af_nicole", "Nicole", "Soft & calm", "Female"),
            Voice("am_michael", "Michael", "Clear & confident", "Male"),
            Voice("am_fenrir", "Fenrir", "Deep & dramatic", "Male"),
            Voice("bf_emma", "Emma", "British, polished", "Female"),
            Voice("bm_george", "George", "British, documentary", "Male"),
        ),
    ),
    Engine(
        id="piper",
        kind="tts",
        label="Piper TTS",
        modules=("piper",),
        downloads=tuple(
            d
            for path in PIPER_VOICE_FILES.values()
            for d in (
                Download("rhasspy/piper-voices", filename=f"{path}.onnx"),
                Download("rhasspy/piper-voices", filename=f"{path}.onnx.json"),
            )
        ),
        size="0.3 GB",
        note="Runs on the CPU, extremely fast. Slightly robotic.",
        voices=(
            Voice("en_US-lessac-medium", "Lessac", "Neutral narrator", "Female"),
            Voice("en_US-ryan-high", "Ryan", "Clear & steady", "Male"),
            Voice("en_US-amy-medium", "Amy", "Friendly", "Female"),
            Voice("en_GB-alan-medium", "Alan", "British", "Male"),
        ),
    ),
    Engine(
        id="xtts",
        kind="tts",
        label="Coqui XTTS-v2",
        modules=("TTS",),
        size="1.9 GB",
        note="Very natural, multilingual. Requires accepting the Coqui CPML licence (COQUI_TOS_AGREED=1).",
        voices=(
            Voice("Ana Florence", "Ana Florence", "Warm storyteller", "Female"),
            Voice("Claribel Dervla", "Claribel", "Bright & lively", "Female"),
            Voice("Daisy Studious", "Daisy", "Calm explainer", "Female"),
            Voice("Damien Black", "Damien", "Deep & dark", "Male"),
            Voice("Craig Gordon", "Craig", "Documentary", "Male"),
            Voice("Viktor Eka", "Viktor", "Strong & direct", "Male"),
        ),
    ),
    Engine(
        id="melo",
        kind="tts",
        label="MeloTTS",
        # Runs in its own venv (MELO_PYTHON) because it pins old library versions.
        modules=(),
        size="0.6 GB (+0.5 GB dictionary)",
        note="Fast and clean. Lives in a separate venv because of its pinned dependencies.",
        voices=(
            Voice("EN-US", "American", "Neutral", "Female"),
            Voice("EN-BR", "British", "Neutral", "Female"),
            Voice("EN-AU", "Australian", "Neutral", "Female"),
            Voice("EN-INDIA", "Indian", "Neutral", "Female"),
            Voice("EN-Default", "Default", "Neutral", "Male"),
        ),
    ),
    Engine(
        id="bark",
        kind="tts",
        label="Bark",
        modules=("transformers", "soundfile"),
        downloads=(Download("suno/bark-small"),),
        size="1.7 GB",
        note="Most expressive (can laugh, sigh) but slow and sometimes unstable.",
        voices=tuple(
            Voice(f"v2/en_speaker_{i}", f"Speaker {i}", desc, kind)
            for i, desc, kind in (
                (0, "Calm", "Male"),
                (1, "Energetic", "Male"),
                (3, "Narrator", "Male"),
                (6, "Deep & steady", "Male"),
                (9, "Soft", "Female"),
            )
        ),
    ),
)

# ---------------------------------------------------------------------- #
# Text to image
# ---------------------------------------------------------------------- #
SDXL_VAE_FIX = Download("madebyollin/sdxl-vae-fp16-fix", allow=("config.json", "diffusion_pytorch_model.safetensors"))
FLUX_GGUF = Download("city96/FLUX.1-schnell-gguf", filename="flux1-schnell-Q4_K_S.gguf")

IMAGE_ENGINES: tuple[Engine, ...] = (
    Engine(
        id="sdxl-turbo",
        kind="image",
        label="SDXL Turbo",
        modules=("diffusers", "transformers", "accelerate"),
        downloads=(Download("stabilityai/sdxl-turbo", allow=_FP16), SDXL_VAE_FIX),
        size="7 GB",
        note="4 steps, ~5 s per image. Recommended default.",
    ),
    Engine(
        id="sdxl",
        kind="image",
        label="Stable Diffusion XL",
        modules=("diffusers", "transformers", "accelerate"),
        downloads=(Download("stabilityai/stable-diffusion-xl-base-1.0", allow=_FP16), SDXL_VAE_FIX),
        size="7 GB",
        note="Best detail of the SD family, ~40-60 s per image.",
    ),
    Engine(
        id="sd15",
        kind="image",
        label="Stable Diffusion 1.5",
        modules=("diffusers", "transformers", "accelerate"),
        downloads=(Download("stable-diffusion-v1-5/stable-diffusion-v1-5", allow=_FP16 + ("feature_extractor/*",)),),
        size="2 GB",
        note="Lightest and fastest. Lower quality.",
    ),
    Engine(
        id="flux-schnell",
        kind="image",
        label="FLUX.1-schnell",
        modules=("diffusers", "transformers", "accelerate", "gguf", "sentencepiece"),
        downloads=(
            Download(
                "black-forest-labs/FLUX.1-schnell",
                allow=(
                    "model_index.json", "scheduler/*", "text_encoder/*", "text_encoder_2/*",
                    "tokenizer/*", "tokenizer_2/*", "vae/*", "transformer/config.json",
                ),
            ),
            FLUX_GGUF,
        ),
        size="17 GB",
        note="Best prompt following. Heaviest: 1-3 min per image on 8 GB, needs a big page file.",
    ),
)

# ---------------------------------------------------------------------- #
# Image to video
# ---------------------------------------------------------------------- #
VIDEO_ENGINES: tuple[Engine, ...] = (
    Engine(
        id="ltx-video",
        kind="video",
        label="LTX-Video 2B",
        modules=("diffusers", "transformers", "accelerate", "sentencepiece", "imageio"),
        downloads=(
            Download(
                "Lightricks/LTX-Video",
                allow=("model_index.json", "scheduler/*", "text_encoder/*", "tokenizer/*", "transformer/*", "vae/*"),
            ),
        ),
        size="19 GB",
        note="Fastest real image-to-video, ~2-4 min per clip. Recommended default.",
    ),
    Engine(
        id="svd-xt",
        kind="video",
        label="Stable Video Diffusion XT",
        modules=("diffusers", "transformers", "accelerate", "imageio"),
        downloads=(Download("stabilityai/stable-video-diffusion-img2vid-xt", allow=_FP16),),
        size="5 GB",
        note="Keeps the image very faithfully; mostly camera motion. ~3-5 min per clip.",
    ),
    Engine(
        id="wan-1.3b",
        kind="video",
        label="Wan 2.1 1.3B (VACE)",
        modules=("diffusers", "transformers", "accelerate", "ftfy", "sentencepiece", "imageio"),
        downloads=(Download("Wan-AI/Wan2.1-VACE-1.3B-diffusers", allow=_SUBFOLDER_WEIGHTS),),
        size="18 GB",
        note="Best motion quality, slowest: 6-12 min per clip.",
    ),
    Engine(
        id="cogvideox-2b",
        kind="video",
        label="CogVideoX-2B (text-to-video)",
        modules=("diffusers", "transformers", "accelerate", "sentencepiece", "imageio"),
        downloads=(Download("THUDM/CogVideoX-2b", allow=_SUBFOLDER_WEIGHTS),),
        size="13 GB",
        note="2B is text-to-video only: it animates the scene prompt, NOT your image. Landscape 720x480.",
    ),
)

ENGINES: dict[str, Engine] = {e.id: e for e in (*TTS_ENGINES, *IMAGE_ENGINES, *VIDEO_ENGINES)}


def engine_ids(kind: str) -> tuple[str, ...]:
    """Ids of every engine of ``kind`` ("tts", "image" or "video"), in display order."""
    return tuple(e.id for e in ENGINES.values() if e.kind == kind)


# ---------------------------------------------------------------------- #
# Compilation (runs in the main backend, not the GPU worker)
# ---------------------------------------------------------------------- #
COMPILERS: dict[str, str] = {
    "ffmpeg": "FFmpeg",
    "moviepy": "MoviePy",
    "kdenlive": "Kdenlive (MLT)",
}
