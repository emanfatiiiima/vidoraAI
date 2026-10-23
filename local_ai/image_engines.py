"""
Local text-to-image engines (diffusers). Each returns PNG bytes.

Every engine renders a vertical 9:16-ish frame (like the cloud providers); the
final render crops/scales it to the output size anyway. Memory settings are
tuned for an 8 GB Turing card (RTX 20xx): fp16 weights, CPU offload for the
big models and the fp16-safe SDXL VAE (the stock one produces black images
in fp16).
"""

from __future__ import annotations

import io
import random

from local_ai.catalog import FLUX_GGUF
from local_ai.runtime import SLOT, EngineInputError, cuda_device

NEGATIVE_PROMPT = "blurry, low quality, lowres, watermark, text, logo, signature, deformed, extra limbs, jpeg artifacts"


def generate(engine: str, prompt: str, seed: int | None = None) -> bytes:
    prompt = prompt.strip()
    if not prompt:
        raise EngineInputError("Prompt is required.")
    loader, run = _ENGINES[engine]
    seed = random.randint(0, 2**31 - 1) if seed is None else seed
    with SLOT.use(engine, loader) as pipe:
        image = run(pipe, prompt, _generator(seed))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _generator(seed: int):
    import torch

    return torch.Generator("cpu").manual_seed(seed)


def _sdxl_vae():
    import torch
    from diffusers import AutoencoderKL

    return AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)


# ---------------------------------------------------------------------- #
# Stable Diffusion 1.5
# ---------------------------------------------------------------------- #
def _load_sd15():
    import torch
    from diffusers import StableDiffusionPipeline

    pipe = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        variant="fp16",
        safety_checker=None,
        requires_safety_checker=False,
    )
    return pipe.to(cuda_device())


def _run_sd15(pipe, prompt, generator):
    # 512x768: SD 1.5 was trained at 512 px; taller frames duplicate subjects.
    return pipe(prompt, negative_prompt=NEGATIVE_PROMPT, width=512, height=768,
                num_inference_steps=30, guidance_scale=7.0, generator=generator).images[0]


# ---------------------------------------------------------------------- #
# SDXL Turbo
# ---------------------------------------------------------------------- #
def _load_sdxl_turbo():
    import torch
    from diffusers import AutoPipelineForText2Image

    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo", vae=_sdxl_vae(), torch_dtype=torch.float16, variant="fp16"
    )
    cuda_device()
    pipe.enable_model_cpu_offload()
    return pipe


def _run_sdxl_turbo(pipe, prompt, generator):
    # Turbo ignores negative prompts and guidance; 4 steps is its sweet spot.
    return pipe(prompt, width=576, height=1024, num_inference_steps=4,
                guidance_scale=0.0, generator=generator).images[0]


# ---------------------------------------------------------------------- #
# SDXL base
# ---------------------------------------------------------------------- #
def _load_sdxl():
    import torch
    from diffusers import StableDiffusionXLPipeline

    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", vae=_sdxl_vae(), torch_dtype=torch.float16, variant="fp16"
    )
    cuda_device()
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_tiling()
    return pipe


def _run_sdxl(pipe, prompt, generator):
    return pipe(prompt, negative_prompt=NEGATIVE_PROMPT, width=768, height=1344,
                num_inference_steps=30, guidance_scale=6.5, generator=generator).images[0]


# ---------------------------------------------------------------------- #
# FLUX.1-schnell (4-bit GGUF transformer so it fits in 8 GB)
# ---------------------------------------------------------------------- #
def _load_flux():
    import torch
    from diffusers import FluxPipeline, FluxTransformer2DModel, GGUFQuantizationConfig
    from huggingface_hub import hf_hub_download

    cuda_device()
    gguf_path = hf_hub_download(FLUX_GGUF.repo, FLUX_GGUF.filename)
    # bfloat16: FLUX overflows to black/noisy images in float16. Turing emulates
    # bf16, which is slower but correct.
    transformer = FluxTransformer2DModel.from_single_file(
        gguf_path,
        quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
        torch_dtype=torch.bfloat16,
        config="black-forest-labs/FLUX.1-schnell",
        subfolder="transformer",
    )
    pipe = FluxPipeline.from_pretrained(
        "black-forest-labs/FLUX.1-schnell", transformer=transformer, torch_dtype=torch.bfloat16
    )
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    return pipe


def _run_flux(pipe, prompt, generator):
    return pipe(prompt, width=576, height=1024, num_inference_steps=4, guidance_scale=0.0,
                max_sequence_length=256, generator=generator).images[0]


_ENGINES = {
    "sd15": (_load_sd15, _run_sd15),
    "sdxl-turbo": (_load_sdxl_turbo, _run_sdxl_turbo),
    "sdxl": (_load_sdxl, _run_sdxl),
    "flux-schnell": (_load_flux, _run_flux),
}
