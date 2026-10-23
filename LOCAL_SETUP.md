# VidoraAI, fully local: step-by-step setup

This guide sets up VidoraAI so **every step runs on your own machine**, with no API keys and no cloud:

| Step in the app | Local options | Runs in |
|---|---|---|
| Topics + Script | Any **Ollama** model (Qwen3, Llama 3.1, Gemma 3, Mistral, ...) | Ollama |
| Voice-over | **Kokoro**, **Piper**, **Coqui XTTS-v2**, **MeloTTS**, **Bark** | GPU worker |
| Images | **SDXL Turbo**, **SDXL**, **Stable Diffusion 1.5**, **FLUX.1-schnell** | GPU worker |
| Video clips | **LTX-Video 2B**, **Stable Video Diffusion XT**, **Wan 2.1 1.3B (VACE)**, **CogVideoX-2B** | GPU worker |
| Final render | **FFmpeg**, **MoviePy**, **Kdenlive (MLT)** | Backend |

Tuned for: **RTX 2060 SUPER 8 GB (Turing), Ryzen 5 3600, 16 GB RAM**.

Follow the steps **in order**. Each one ends with a ✅ check. Don't move on until it passes.

---

## How the pieces fit together

```
Browser (localhost:3000)
   │
   ▼
Backend  (FastAPI, .venv, port 8000) ──► Ollama (port 11434)         text
   │                                ──► GPU worker (port 8001)       voice / images / video
   │                                       local_ai/.venv  (PyTorch + CUDA)
   │                                       local_ai/.venv-melo  (MeloTTS only)
   └──► FFmpeg / MoviePy / Kdenlive's melt                           final render
```

The **GPU worker** is a separate program with its own Python environment because the model libraries
(PyTorch, diffusers, Coqui, Kokoro) are huge and clash with each other. It keeps **one model on the GPU at
a time**, asks Ollama to release VRAM before loading a model, and unloads idle models after 3 minutes.
This is what lets everything fit on an 8 GB card.

### ⚠️ Run the models on the machine with the RTX 2060 SUPER

The models need that GPU. This repo's current PC reports an **MX130 (2 GB)**, which can't run them.
Pick one layout:

- **A. Everything on the GPU machine** (simplest). Clone the repo there and follow this guide there.
- **B. App on this PC, models on the GPU machine.** On the GPU machine, do steps 1 to 9 (Ollama + worker only).
  Then expose them to your local network:
  - Worker: set `LOCAL_AI_HOST=0.0.0.0` before starting it (step 10).
  - Ollama: set the environment variable `OLLAMA_HOST=0.0.0.0` and restart Ollama.
  - In this PC's `.env`: `LOCAL_AI_URL=http://<gpu-machine-ip>:8001` and `OLLAMA_URL=http://<gpu-machine-ip>:11434`.
  - Allow ports 8001 and 11434 in the GPU machine's firewall. **Only do this on a trusted home network**,
    because neither service has a password.

Your pasted specs (driver `595.71.05`) look like **Linux** output. This guide gives **Windows** commands first,
with 🐧 **Linux** equivalents wherever they differ.

---

## Step 1: Install the base programs

| Program | Windows | 🐧 Linux (Ubuntu/Debian) |
|---|---|---|
| NVIDIA driver | Already installed (driver 595, CUDA 13.2 is fine) | Already installed |
| Python **3.11** (worker) | `py install 3.11` (or the python.org installer) | `sudo apt install python3.11 python3.11-venv` (deadsnakes PPA if missing) |
| Python **3.10** (MeloTTS only, optional) | `py install 3.10` | `sudo apt install python3.10 python3.10-venv` |
| Git | Already installed | `sudo apt install git` |
| Node.js 20+ | Already installed | `sudo apt install nodejs npm` |
| FFmpeg | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` |
| Ollama | Already installed (`ollama.com/download`) | `curl -fsSL https://ollama.com/install.sh \| sh` |
| Kdenlive (optional) | `winget install KDE.Kdenlive` | `sudo apt install kdenlive melt` |

> Why Python 3.11 and not 3.14? Kokoro and Coqui TTS don't support 3.13+ yet. The main backend keeps
> using your existing `.venv` (3.14). Only the worker uses 3.11.

**Close and reopen your terminal** after installing (so PATH updates), then:

✅ Check: each of these prints a version:

```bash
nvidia-smi
```
```bash
py -3.11 --version
```
```bash
ffmpeg -version
```
```bash
ollama --version
```

(🐧 use `python3.11 --version`.)

**Disk space:** have **~150 GB free on an SSD** if you want every model (about 30 GB is enough for the
recommended set). To keep models off `C:`, set the environment variable `HF_HOME=D:\hf-cache` (any folder)
**before** step 9, and keep it set whenever you start the worker.

---

## Step 2: Give Windows enough virtual memory (important with 16 GB RAM)

FLUX, LTX-Video, Wan and CogVideoX load a ~10 GB text encoder into **system RAM** while they start.
With 16 GB RAM this crashes ("out of memory", "paging file is too small", or the worker just dies) unless
the page file is large.

**Windows:**
1. Press `Win`, type **"Advanced system settings"** and open it.
2. **Performance** → **Settings** → **Advanced** → **Virtual memory** → **Change**.
3. Untick **"Automatically manage..."**, select your **SSD** drive, choose **Custom size**:
   Initial **32768** MB, Maximum **65536** MB → **Set** → **OK**.
4. **Restart** the PC.

🐧 **Linux:** add a 32 GB swap file:
```bash
sudo fallocate -l 32G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
```
(Add `/swapfile none swap sw 0 0` to `/etc/fstab` to keep it after reboots.)

✅ Check: Task Manager → Performance → Memory shows **"Committed: x / ~80 GB"**.

> Optional: Windows long paths. Some pip packages have deep folder paths. As administrator, run
> `reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f`, then reboot.

---

## Step 3: Main app (backend + frontend)

From the project folder (`vidoraAI`):

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```
```bash
npm --prefix frontend install
```

(🐧 `.venv/bin/python -m pip install -r requirements.txt`. If there's no `.venv` yet:
`python3 -m venv .venv` first.)

Create `.env` from `.env.example` if you haven't, and set these lines:

```ini
LOCAL_ONLY=true
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_DEFAULT_MODEL=qwen3:8b
LOCAL_AI_URL=http://127.0.0.1:8001
FFMPEG_PATH=ffmpeg
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
```

`LOCAL_ONLY=true` hides every cloud AI in the popup. Use `VIDEO_WIDTH=1920` / `VIDEO_HEIGHT=1080` for
landscape (classic YouTube) videos.

✅ Check: `.venv\Scripts\python -m pytest` → all tests pass.

---

## Step 4: Create the GPU worker environment

Run these **from the project folder**, one at a time.

**Windows:**
```bash
py -3.11 -m venv local_ai\.venv
```
```bash
local_ai\.venv\Scripts\python -m pip install --upgrade pip wheel
```
```bash
local_ai\.venv\Scripts\python -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
```
```bash
local_ai\.venv\Scripts\python -m pip install -r local_ai\requirements.txt -c local_ai\constraints.txt
```

🐧 **Linux:**
```bash
python3.11 -m venv local_ai/.venv
```
```bash
local_ai/.venv/bin/python -m pip install --upgrade pip wheel
```
```bash
local_ai/.venv/bin/python -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
```
```bash
local_ai/.venv/bin/python -m pip install -r local_ai/requirements.txt -c local_ai/constraints.txt
```

Notes that prevent the most common errors:

- **Install torch first, from the `cu128` index.** A plain `pip install torch` gives you a CPU-only build
  and every model will fail with "PyTorch can't see a CUDA GPU". `constraints.txt` stops later installs
  from swapping it. CUDA 12.8 wheels run fine on your CUDA 13.2 driver.
- If the requirements install fails with a **"ResolutionImpossible"** message that mentions `torch`, some
  package wants a newer torch. Tell me the message and I'll bump the pins together.

✅ Check: this must print `True NVIDIA GeForce RTX 2060 SUPER`:
```bash
local_ai\.venv\Scripts\python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

---

## Step 5: Hugging Face login (needed for a few gated models)

Some models need you to accept their licence on the website first:

| Model | Page to open and click "Agree and access" |
|---|---|
| Stable Video Diffusion XT | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt |
| SDXL Turbo | https://huggingface.co/stabilityai/sdxl-turbo |
| FLUX.1-schnell | https://huggingface.co/black-forest-labs/FLUX.1-schnell |

1. Create a free account at huggingface.co and accept the pages above (only the models you want).
2. **Settings** → **Access Tokens** → **Create new token** → type **Read**.
3. Log in (paste the token when asked):
```bash
local_ai\.venv\Scripts\hf auth login
```

✅ Check: `local_ai\.venv\Scripts\hf auth whoami` prints your username.

---

## Step 6 (optional): MeloTTS environment

MeloTTS pins old library versions, so it gets its own small environment on **Python 3.10**.
Skip this step if you don't want MeloTTS.

**Windows:**
```bash
py -3.10 -m venv local_ai\.venv-melo
```
```bash
local_ai\.venv-melo\Scripts\python -m pip install --upgrade pip wheel
```
```bash
local_ai\.venv-melo\Scripts\python -m pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
```
```bash
local_ai\.venv-melo\Scripts\python -m pip install -r local_ai\requirements-melo.txt
```

🐧 Same commands with `python3.10` and `local_ai/.venv-melo/bin/python`.

The worker finds it automatically at `local_ai/.venv-melo`. If you put it elsewhere, set `MELO_PYTHON`
to that Python before starting the worker.

✅ Check: `local_ai\.venv-melo\Scripts\python -c "import melo; print('ok')"` prints `ok`.

---

## Step 7 (optional): Coqui XTTS-v2 licence

XTTS-v2 is released under the **Coqui Public Model License (non-commercial use only)**. Read
https://coqui.ai/cpml. If you agree, set this variable **in the terminal where you download models
(step 9) and start the worker (step 10)**:

```bash
set COQUI_TOS_AGREED=1
```
(PowerShell: `$env:COQUI_TOS_AGREED="1"`. 🐧 `export COQUI_TOS_AGREED=1`.)

Without it, XTTS-v2 shows as "not ready" in the popup and everything else still works.

---

## Step 8: Pull Ollama text models

Ollama models that fit an 8 GB card (any model you pull appears in the popup automatically):

| Model | Size | Use it for |
|---|---|---|
| `qwen3:8b` | 5.2 GB | **Best all-rounder**: great scripts, reliable JSON. Recommended. |
| `llama3.1:8b` | 4.9 GB | Natural, conversational narration |
| `gemma3:4b` | 3.3 GB | Fastest; good for topic ideas |
| `mistral:7b` | 4.4 GB | You already have `mistral:latest`: fine for scripts |
| `qwen2.5:7b` | 4.7 GB | Very good at following formats |
| `gemma3:12b` | 8.1 GB | Best writing quality, but spills into RAM (slower) |

```bash
ollama pull qwen3:8b
```
```bash
ollama pull gemma3:4b
```

✅ Check: `ollama run qwen3:8b "Say hi in five words"` answers.

> Qwen3 "thinks" before answering, which takes a bit longer but gives better scripts. VidoraAI removes the
> thinking text automatically.

---

## Step 9: Download the voice, image and video models

Always run downloads with the worker's Python, from the project folder. First see what exists:

```bash
local_ai\.venv\Scripts\python -m local_ai.download --list
```

Then download the **recommended set** (Kokoro + Piper + SDXL Turbo + LTX-Video, ~27 GB):

```bash
local_ai\.venv\Scripts\python -m local_ai.download recommended
```

Add any others by id (any time later, too):

```bash
local_ai\.venv\Scripts\python -m local_ai.download sdxl flux-schnell svd-xt wan-1.3b cogvideox-2b bark
```
```bash
local_ai\.venv\Scripts\python -m local_ai.download xtts melo
```

Or everything (~110 GB): `local_ai\.venv\Scripts\python -m local_ai.download all`

| id | Download | Notes |
|---|---|---|
| `kokoro` | 0.4 GB | Voice: best quality for the speed |
| `piper` | 0.3 GB | Voice: CPU, instant, a bit robotic |
| `xtts` | 1.9 GB | Voice: very natural (needs step 7) |
| `melo` | 1.1 GB | Voice: fast, clean (needs step 6) |
| `bark` | 1.7 GB | Voice: most expressive, slow, sometimes odd |
| `sdxl-turbo` | 7 GB | Images: 4 steps, about 5 s each |
| `sdxl` | 7 GB | Images: best SD detail, about 45 s each |
| `sd15` | 2 GB | Images: lightest, lower quality |
| `flux-schnell` | 17 GB | Images: best prompt-following, 1 to 3 min each |
| `ltx-video` | 19 GB | Video: fastest real image-to-video |
| `svd-xt` | 5 GB | Video: most faithful to the image (camera moves) |
| `wan-1.3b` | 18 GB | Video: best motion, slowest |
| `cogvideox-2b` | 13 GB | Video: **text-to-video only**, ignores your image, landscape |

Downloads **resume** if interrupted: just run the same command again. A model only shows as available in
the app once its download finished completely.

If a download says **401 / gated**, you skipped step 5 for that model.

✅ Check: `--list` shows `ready` next to what you downloaded.

---

## Step 10: Start everything (every time you use the app)

Use **four terminals**, from the project folder, in this order:

**1. Ollama**: usually already running (tray icon). If not: `ollama serve`

**2. GPU worker** (set `COQUI_TOS_AGREED` / `HF_HOME` here first if you use them):
```bash
local_ai\.venv\Scripts\python -m local_ai
```
Wait for `Uvicorn running on http://127.0.0.1:8001`.

**3. Backend:**
```bash
.venv\Scripts\python -m fastapi_backend
```

**4. Frontend:**
```bash
npm --prefix frontend run dev
```

Open **http://localhost:3000**.

✅ Check: http://127.0.0.1:8001/health in the browser shows `"cuda": true` and `"available": true`
for every model you downloaded.

---

## Step 11: Choose your AIs in the app

The **Choose your AIs** popup now lists the local models (🖴 icon). An option is crossed out with the
reason when it isn't ready (worker not running, model not downloaded, etc.), so you can fix it and reopen
the popup.

Recommended combinations for the RTX 2060 SUPER:

| Goal | Topics / Script | Voice | Images | Video | Render |
|---|---|---|---|---|---|
| **Best balance** (recommended) | Ollama · qwen3:8b | Kokoro | SDXL Turbo | LTX-Video 2B | FFmpeg |
| **Fastest test run** | Ollama · gemma3:4b | Piper | SD 1.5 | SVD XT | FFmpeg |
| **Maximum quality** (slow) | Ollama · qwen3:8b | XTTS-v2 | FLUX.1-schnell or SDXL | Wan 2.1 1.3B | FFmpeg |
| **Hand-edit afterwards** | any | any | any | any | Kdenlive (MLT) |

Rough timings on this GPU for a **1-minute video with 6 scenes**:

| Step | Time |
|---|---|
| Topics + script (qwen3:8b) | 1 to 2 min |
| Narration (Kokoro) | 10 to 30 s |
| 6 images (SDXL Turbo) | about 1 min (the first one loads the model, about 30 s) |
| 6 clips (LTX-Video) | 15 to 25 min |
| 6 clips (Wan 2.1) | 40 to 70 min |
| Final render (FFmpeg) | under 1 min |

---

## Step 12: Tips for a great final video

1. **Scenes vs clip length.** Clips are 2 to 6 s long and the render loops each one back and forth to cover
   its part of the narration. Aim for **one scene per 5 to 8 s of narration** (for example 8 to 10 scenes
   for a 1-minute video). Fewer scenes means visible looping.
2. **Scene timing follows the voice.** Each scene stays on screen in proportion to the number of words it
   narrates, so visuals change when the narration moves on.
3. **Edit the image prompts in Step 5** before generating. Concrete subjects, lighting and camera words
   ("close-up", "wide shot", "golden hour") help both the image and the video model.
4. **Regenerate the odd one out.** Every image and clip has its own regenerate button. Seeds are random,
   so a second try often fixes hands, faces or weird motion.
5. **The voice speed slider** works for every local voice (0.7× to 1.3×). Pitch only applies to UnrealSpeech,
   so it is hidden for local voices.
6. **Vertical vs landscape.** Images and clips are generated vertical (9:16). The renderer scales and
   center-crops to `VIDEO_WIDTH × VIDEO_HEIGHT`, so landscape output crops top and bottom.
7. **Kdenlive render** also saves an editable project next to the video:
   `media/final/<id>_kdenlive/project.mlt` with all scene clips and the narration. In Kdenlive use
   **Project → Add Clip** and pick `project.mlt`, or open it directly, to add music, titles and transitions.
8. Your files live in `media/` (`audio/`, `clips/`, `final/`). Step 8 "Download" bundles everything into a ZIP.
   Delete old files in `media/` from time to time; it grows quickly.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Popup: "The local AI worker is not running" | Start it (step 10, terminal 2). With layout B, check `LOCAL_AI_URL` and the firewall. |
| Popup: "Model not downloaded yet" | Run the `python -m local_ai.download <id>` command shown, then reopen the popup. |
| "PyTorch can't see a CUDA GPU" | Torch is the CPU build. Redo the torch line of step 4 (with `--index-url .../cu128`), then the requirements line with `-c local_ai\constraints.txt`. |
| "... ran out of GPU/system memory" | Close games, OBS and browser tabs playing video. Check the page file (step 2). Try a lighter model (SDXL Turbo instead of FLUX, LTX instead of Wan). The worker already unloads Ollama and the previous model for you. |
| Worker window closes or freezes during FLUX / LTX / Wan / CogVideoX loading | System RAM ran out. Step 2 page file / swap, then restart the worker. |
| Black or noisy images | Should not happen: the worker uses the fp16-safe SDXL VAE and bf16 for FLUX. If it does, regenerate. If it keeps happening, tell me the model. |
| Download error 401 / "gated repo" | Step 5: accept the licence on the model page, then `hf auth login`. |
| XTTS-v2 "not ready" | Step 7: `COQUI_TOS_AGREED=1` in the worker's terminal, then `python -m local_ai.download xtts`. |
| MeloTTS fails with `unidic` or `nltk` errors | Run `python -m local_ai.download melo` again (it downloads the dictionary and NLTK data). |
| Kokoro error about `en_core_web_sm` | `local_ai\.venv\Scripts\python -m spacy download en_core_web_sm` |
| Bark voice sounds strange | Normal for Bark sometimes. Regenerate or use Kokoro / XTTS. |
| Render: "FFmpeg not found" | Step 1, then **restart the backend terminal** (PATH is read at start). Or set `FFMPEG_PATH` to the full path of `ffmpeg.exe`. |
| Render: "Kdenlive's 'melt' renderer not found" | Install Kdenlive, or set `MELT_PATH` in `.env` to `melt.exe` (Windows: `C:\Program Files\kdenlive\bin\melt.exe`). |
| Script or topics take minutes | First call loads the model into VRAM. If the GPU is busy with an image or video model, Ollama falls back to the CPU. The worker frees the GPU after 3 minutes idle (`LOCAL_AI_IDLE_UNLOAD_SECONDS`). |
| Ollama answers are cut off | Raise `OLLAMA_NUM_CTX` in `.env` (default 8192). |
| `pip` "ResolutionImpossible" in step 4 | Send me the full message. Pins in `local_ai/constraints.txt` may need a bump. |
| Windows warning about symlinks during downloads | Harmless. Hugging Face copies files instead of linking them. |

---

## Model licences (check before commercial use)

| Model | Licence |
|---|---|
| Kokoro, Wan 2.1, CogVideoX-2B, FLUX.1-schnell | Apache 2.0 |
| MeloTTS, Bark | MIT |
| Piper | MIT engine; each voice has its own licence (see its model card) |
| Coqui XTTS-v2 | Coqui Public Model License (**non-commercial**) |
| Stable Diffusion 1.5, SDXL | CreativeML OpenRAIL-M / OpenRAIL++-M |
| SDXL Turbo, Stable Video Diffusion XT | Stability AI Community License (free under $1M yearly revenue) |
| LTX-Video | Lightricks open-weights licence (see the model card) |
| Ollama models | Each model's own licence (`ollama show <model> --license`) |
