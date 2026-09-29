# VidoraAI

An AI-powered YouTube video production studio (branded **DugarAI** in the UI).
It takes you from a niche idea to a finished video through a guided pipeline:

| # | Step       | What happens                                                   | Powered by                     |
|---|------------|----------------------------------------------------------------|--------------------------------|
| 1 | Start      | Choose niche, style, duration, aspect ratio, scene count       | —                              |
| 2 | Topic      | Basic / unique / trending topic ideas (news + Google Trends)   | Gemini → OpenAI → Groq, SerpApi |
| 3 | Narrative  | Voice-over script + summary, export as TXT / DOCX              | LLM, python-docx               |
| 4 | Audio      | Narration with 6 voices, speed & pitch controls                | UnrealSpeech                   |
| 5 | Visuals    | Script split into scenes, image prompt + image per scene       | LLM, Gemini / DALL-E / Pollinations |
| 6 | Motion     | Scene image → video clip *(simulated)*                         | placeholder                    |
| 7 | Finalize   | Stitch clips + narration into the final video *(simulated)*    | placeholder                    |
| 8 | Download   | Preview and download the result                                | —                              |

---

## Architecture

The project is split into three independent layers:

```
vidoraAI/
├── core/               # Python – ALL business logic (no web framework)
├── fastapi_backend/    # Python – thin HTTP API on top of core
├── frontend/           # React + TypeScript + Vite – the UI
├── tests/              # pytest tests for core and the API
├── requirements.txt    # Python runtime deps
├── requirements-dev.txt
├── pyproject.toml      # pytest / ruff config
└── .env.example        # all supported environment variables
```

```
 Browser (React)  ──HTTP /api/*──►  fastapi_backend  ──calls──►  core  ──►  Gemini / OpenAI / Groq
   frontend/                          routers, schemas,           services,    SerpApi, UnrealSpeech,
   services/api.ts                    error mapping               prompts      Google News, Pollinations
```

**Rules of thumb**

- **`core/`** knows nothing about HTTP. It can be used from a script, a worker or a test.
- **`fastapi_backend/`** only validates input, calls a core service and returns the result.
- **`frontend/`** only renders UI. It never holds API keys or prompts; every server call
  goes through [`frontend/src/services/api.ts`](frontend/src/services/api.ts).

### `core/` – business logic

| Path                      | Responsibility                                                    |
|---------------------------|-------------------------------------------------------------------|
| `config.py`               | Typed settings loaded from `.env` (`Settings`, `get_settings()`)  |
| `exceptions.py`           | Domain errors (`InvalidAIResponseError`, `ExternalServiceError`…) |
| `prompts.py`              | Every LLM prompt template                                         |
| `llm/base.py`             | `LLMProvider` interface, `LLMRequest`, `LLMResponse`              |
| `llm/providers.py`        | Gemini, OpenAI and Groq implementations                           |
| `llm/router.py`           | `LLMRouter` – tries providers in order, falls back on failure     |
| `services/topics.py`      | Step 2 – basic / unique / trending topics                         |
| `services/research.py`    | Google Trends (SerpApi) + Google News headlines                   |
| `services/scripts.py`     | Step 3 – script + summary                                         |
| `services/export.py`      | Step 3 – TXT / DOCX export                                        |
| `services/audio.py`       | Step 4 – UnrealSpeech TTS                                         |
| `services/scenes.py`      | Step 5 – scene splitting + image prompts                          |
| `services/images.py`      | Step 5 – image generation with fallbacks                          |
| `services/video.py`       | Steps 6–7 – clip generation + compilation (**simulated**)         |
| `utils/json_parser.py`    | Robust parsing of JSON returned by LLMs                           |
| `container.py`            | `build_services()` – wires settings, SDK clients and services     |

### `fastapi_backend/` – HTTP API

| Path               | Responsibility                                                       |
|--------------------|----------------------------------------------------------------------|
| `main.py`          | `create_app()` factory, CORS, lifespan, serves `frontend/dist` in prod |
| `routers/`         | Endpoints grouped by feature                                         |
| `schemas.py`       | Pydantic request/response models (camelCase JSON ⇄ snake_case Python) |
| `dependencies.py`  | `ServicesDep` – injects core services into routes                    |
| `errors.py`        | Maps core exceptions → HTTP status + `{error, code, details}` body   |

### `frontend/` – React UI

| Path                        | Responsibility                                  |
|-----------------------------|-------------------------------------------------|
| `src/App.tsx`               | App shell, auth pages, step state machine       |
| `src/components/steps/`     | One component per pipeline step                 |
| `src/components/auth/`      | Login / signup / forgot password (mock auth)    |
| `src/services/api.ts`       | Typed client for every backend endpoint         |
| `src/lib/utils.ts`          | `cn()` Tailwind class helper                    |
| `src/index.css`             | Tailwind theme, fonts and shared UI classes     |

---

## API reference

All endpoints are under `/api`. Interactive docs: **http://localhost:8000/docs** (Swagger UI).

| Method | Path                 | Body / query                                  | Returns                         |
|--------|----------------------|-----------------------------------------------|---------------------------------|
| GET    | `/health`            | –                                             | `{status, llmProviders}`        |
| POST   | `/generate`          | `{prompt, systemPrompt?, responseMimeType?}`  | `{text, provider}`              |
| POST   | `/topics/basic`      | `{niche, duration, audience?}`                | `{topics: string[]}`            |
| POST   | `/topics/unique`     | `{niche}`                                     | `{topics: string[]}`            |
| POST   | `/topics/trending`   | `{niche}`                                     | `{topics: string[]}`            |
| GET    | `/trends`            | `?q=`                                         | Raw SerpApi Google Trends JSON  |
| GET    | `/news`              | `?q=`                                         | `{headlines: string[]}`         |
| POST   | `/script`            | `{topic, niche, duration, style}`             | `{script}`                      |
| POST   | `/script/summary`    | `{script}`                                    | `{summary}`                     |
| POST   | `/script/export`     | `{topic, script, format: "txt" \| "docx"}`    | File download                   |
| POST   | `/scenes/split`      | `{script, sceneCount}`                        | `{scenes: string[]}`            |
| POST   | `/scenes/prompt`     | `{text, style}`                               | `{prompt}`                      |
| POST   | `/tts`               | `{text, voice?, speed?, pitch?}`              | UnrealSpeech JSON (`OutputUri`) |
| POST   | `/generate-image`    | `{prompt}`                                    | `{url}`                         |
| POST   | `/generate-video`    | `{imageUrl, prompt}`                          | `{url, status}`                 |
| POST   | `/compile-video`     | `{scenes: [{id, videoUrl}], audioUrl}`        | `{url, status}`                 |

**Errors** always look like this:

```json
{ "error": "AI returned invalid topic format.", "code": "invalid_ai_response", "details": null }
```

| Code                      | HTTP | Meaning                                         |
|---------------------------|------|-------------------------------------------------|
| `invalid_input`           | 400  | Bad input (e.g. empty TTS text)                 |
| `validation_error`        | 422  | Request body failed schema validation           |
| `invalid_ai_response`     | 502  | AI answered in the wrong format                 |
| `external_service_error`  | 502 / 429 | Third-party API failed (429 = rate limited) |
| `provider_not_configured` | 503  | Required API key missing                        |
| `all_providers_failed`    | 503  | Every LLM provider failed / none configured     |

---

## Getting started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm

### 1. Configure environment variables

```bash
cp .env.example .env
```

Fill in the keys you have. **All keys are optional**; missing ones are skipped:

| Variable                | Used for                                   |
|-------------------------|--------------------------------------------|
| `GEMINI_API_KEY`        | Text + image generation (tried first)      |
| `OPENAI_API_KEY`        | Text fallback + DALL-E images              |
| `GROQ_API_KEY`          | Text fallback                              |
| `LLM_PROVIDER_ORDER`    | Provider order, default `gemini,openai,groq` |
| `SERPAPI_KEY`           | Google Trends (simulated if missing)       |
| `UNREAL_SPEECH_API_KEY` | Text-to-speech (required for Step 4)       |

You need at least one of the Gemini, OpenAI or Groq keys for text generation. Model names can be
overridden too (see `.env.example`).

### 2. Install the backend

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 3. Install the frontend

```bash
cd frontend
npm install
```

### 4. Run in development (two terminals)

**Terminal 1: backend** (from the project root, venv activated):

```bash
uvicorn fastapi_backend.main:app --reload --port 8000
```

**Terminal 2: frontend:**

```bash
cd frontend
npm run dev
```

Open **http://localhost:3000**. Vite proxies every `/api/*` request to the backend on port 8000
(change the target with `VITE_API_PROXY_TARGET`).

> Demo login: any `@gmail.com` address with password `1234` (authentication is mocked in the UI).

### 5. Run in production (single process)

```bash
cd frontend && npm run build && cd ..
uvicorn fastapi_backend.main:app --host 0.0.0.0 --port 8000
```

When `frontend/dist` exists, FastAPI serves the built UI at `/` and the API at `/api`.

---

## Testing & quality checks

```bash
pytest                      # backend tests (no real API calls, uses fake providers)
cd frontend && npm run lint # TypeScript type-check
cd frontend && npm run build
```

---

## Common tasks

| I want to…                              | Where                                                                   |
|-----------------------------------------|-------------------------------------------------------------------------|
| Change what the AI writes               | `core/prompts.py`                                                       |
| Add an LLM provider (e.g. Ollama)       | New class in `core/llm/providers.py`, register it in `core/container.py` |
| Add a new feature endpoint              | Service in `core/services/`, route in `fastapi_backend/routers/`, function in `frontend/src/services/api.ts` |
| Make video generation real              | Implement `core/services/video.py` (Luma / Runway / FFmpeg)             |
| Change colors / fonts                   | `frontend/src/index.css`                                                |

See **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** for step-by-step walkthroughs.

---

## Known limitations

- **Video generation and compilation are simulated.** They return placeholder clips (see `core/services/video.py`).
- **Authentication is mocked** in the frontend (`src/components/auth/Login.tsx`).
- **News headlines are scraped** from Google News HTML, which can break if Google changes its markup.
