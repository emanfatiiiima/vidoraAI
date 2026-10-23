"""
Local image-to-video engines (diffusers). Each returns MP4 bytes.

Clips are short (2-6 s); the final render loops them "ping-pong" style to fit
the narration of each scene. All engines use CPU offload + VAE tiling/slicing
so they fit in 8 GB of VRAM. They need a lot of *system* RAM while loading
(the T5/UMT5 text encoders alone are ~10 GB), so the guide asks for a large
Windows page file.
"""

from __future__ import annotations

import io
import random
import tempfile
from pathlib import Path

from local_ai.runtime import SLOT, cuda_device

VIDEO_NEGATIVE = "worst quality, blurry, jittery, distorted, deformed, static, low resolution, watermark, text"


def generate(engine: str, image_bytes: bytes, prompt: str, seed: int | None = None) -> bytes:
    from diffusers.utils import export_to_video
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    loader, run = _ENGINES[engine]
    seed = random.randint(0, 2**31 - 1) if seed is None else seed
    with SLOT.use(engine, loader) as pipe:
        frames, fps = run(pipe, image, prompt.strip() or "cinematic camera motion", _generator(seed))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "clip.mp4"
        export_to_video(frames, str(out), fps=fps)
        return out.read_bytes()


def _generator(seed: int):
    import torch

    return torch.Generator("cpu").manual_seed(seed)


def _cover(image, width: int, height: int):
    """Scale ``image`` to cover ``width`` x ``height`` and center-crop the overflow."""
    from PIL import Image

    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - width) // 2, (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


# ---------------------------------------------------------------------- #
# LTX-Video 2B
# ---------------------------------------------------------------------- #
def _load_ltx():
    import torch
    from diffusers import LTXImageToVideoPipeline

    cuda_device()
    pipe = LTXImageToVideoPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    return pipe


def _run_ltx(pipe, image, prompt, generator):
    # Width/height must be multiples of 32 and frames 8k+1: 97 frames = 4 s at 24 fps.
    width, height = 480, 832
    frames = pipe(image=_cover(image, width, height), prompt=prompt, negative_prompt=VIDEO_NEGATIVE,
                  width=width, height=height, num_frames=97, num_inference_steps=40,
                  generator=generator).frames[0]
    return frames, 24


# ---------------------------------------------------------------------- #
# Stable Video Diffusion XT
# ---------------------------------------------------------------------- #
def _load_svd():
    import torch
    from diffusers import StableVideoDiffusionPipeline

    cuda_device()
    pipe = StableVideoDiffusionPipeline.from_pretrained(
        "stabilityai/stable-video-diffusion-img2vid-xt", torch_dtype=torch.float16, variant="fp16"
    )
    pipe.enable_model_cpu_offload()
    pipe.unet.enable_forward_chunking()
    return pipe


def _run_svd(pipe, image, prompt, generator):
    # SVD has no text input; the prompt is ignored. 25 frames = ~3.5 s at 7 fps.
    frames = pipe(_cover(image, 576, 1024), width=576, height=1024, num_frames=25,
                  decode_chunk_size=2, motion_bucket_id=127, noise_aug_strength=0.02,
                  generator=generator).frames[0]
    return frames, 7


# ---------------------------------------------------------------------- #
# Wan 2.1 VACE 1.3B (the 1.3B Wan that accepts an image as first frame)
# ---------------------------------------------------------------------- #
def _load_wan():
    import torch
    from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanVACEPipeline

    cuda_device()
    repo = "Wan-AI/Wan2.1-VACE-1.3B-diffusers"
    vae = AutoencoderKLWan.from_pretrained(repo, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanVACEPipeline.from_pretrained(repo, vae=vae, torch_dtype=torch.bfloat16)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=3.0)  # 3.0 for 480p
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    return pipe


def _run_wan(pipe, image, prompt, generator):
    from PIL import Image

    width, height, num_frames = 480, 832, 49  # frames must be 4k+1: 49 = ~3 s at 16 fps
    first = _cover(image, width, height)
    # Frame 0 is given (mask black = keep), the rest is generated (mask white).
    video = [first] + [Image.new("RGB", (width, height), (128, 128, 128))] * (num_frames - 1)
    mask = [Image.new("L", (width, height), 0)] + [Image.new("L", (width, height), 255)] * (num_frames - 1)
    frames = pipe(video=video, mask=mask, prompt=prompt, negative_prompt=VIDEO_NEGATIVE,
                  width=width, height=height, num_frames=num_frames, num_inference_steps=30,
                  guidance_scale=5.0, generator=generator).frames[0]
    return frames, 16


# ---------------------------------------------------------------------- #
# CogVideoX-2B (text-to-video: the 2B model has no image input)
# ---------------------------------------------------------------------- #
def _load_cogvideox():
    import torch
    from diffusers import CogVideoXPipeline

    cuda_device()
    pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-2b", torch_dtype=torch.float16)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    pipe.vae.enable_slicing()
    return pipe


def _run_cogvideox(pipe, image, prompt, generator):
    # Fixed 720x480 output; 49 frames = ~6 s at 8 fps.
    frames = pipe(prompt=prompt, num_frames=49, num_inference_steps=50, guidance_scale=6.0,
                  generator=generator).frames[0]
    return frames, 8


_ENGINES = {
    "ltx-video": (_load_ltx, _run_ltx),
    "svd-xt": (_load_svd, _run_svd),
    "wan-1.3b": (_load_wan, _run_wan),
    "cogvideox-2b": (_load_cogvideox, _run_cogvideox),
}
