# VidoraAI Developer Guide

Practical walkthroughs for extending the project. Read the [README](README.md) first for the
architecture overview and setup.

---

## 1. How a request flows through the system

Example: the user clicks **"Get Unique Ideas"** in Step 2.

1. **UI**: `frontend/src/components/steps/Step2_Topics.tsx` calls `fetchUniqueTopics(niche)`.
2. **API client**: `frontend/src/services/api.ts` sends `POST /api/topics/unique {niche}`.
3. **Router**: `fastapi_backend/routers/topics.py` validates the body (`NicheRequest`) and calls
   `services.topics.generate_unique(niche)`.
4. **Service**: `core/services/topics.py` builds the prompt from `core/prompts.py` and calls
   `LLMRouter.generate(..., json_mode=True)`.
5. **LLM router**: `core/llm/router.py` tries Gemini, then OpenAI, then Groq until one succeeds.
6. The service parses the JSON (`core/utils/json_parser.py`), validates it and returns `list[str]`.
7. If anything fails, a `core.exceptions.*` error is raised and `fastapi_backend/errors.py` turns
   it into `{error, code, details}` with the right HTTP status. The UI switches on `code`/`status`.

---

## 2. Adding a new feature (end to end)

Example: a "generate YouTube title" feature.

**a) Prompt** in `core/prompts.py`:

```python
def title_generator(topic: str) -> str:
    """Catchy YouTube title for a topic."""
    return _clean(f"""
        Write one catchy YouTube title (max 70 characters) for: "{topic}".
        Output ONLY the title.
    """)
```

**b) Service method**, e.g. in `core/services/scripts.py`:

```python
async def generate_title(self, topic: str) -> str:
    """Catchy title for the video."""
    response = await self._llm.generate(prompts.title_generator(topic))
    return response.text.strip()
```

**c) Schemas** in `fastapi_backend/schemas.py`:

```python
class TitleRequest(ApiModel):
    topic: str = Field(min_length=1)

class TitleResponse(ApiModel):
    title: str
```

**d) Route** in `fastapi_backend/routers/scripts.py`:

```python
@router.post("/title", response_model=TitleResponse)
async def generate_title(body: TitleRequest, services: ServicesDep) -> TitleResponse:
    """Catchy YouTube title for the topic."""
    return TitleResponse(title=await services.scripts.generate_title(body.topic))
```

**e) Frontend client** in `frontend/src/services/api.ts`:

```ts
export async function generateTitle(topic: string): Promise<string> {
  const data = await post<{ title: string }>("/script/title", { topic });
  return data.title;
}
```

**f) Test** in `tests/`: use the `client` and `fake_llm` fixtures from `tests/conftest.py`.

> A brand-new service class also needs a field in `Services` and a line in `build_services()`
> (`core/container.py`).

---

## 3. Adding an LLM provider (e.g. local Ollama)

1. Implement the interface in `core/llm/providers.py`:

   ```python
   class OllamaProvider(LLMProvider):
       name = "ollama"

       def __init__(self, http: httpx.AsyncClient, base_url: str, model: str) -> None:
           self._http, self._base_url, self._model = http, base_url, model

       async def generate(self, request: LLMRequest) -> str:
           response = await self._http.post(f"{self._base_url}/api/generate", json={
               "model": self._model,
               "prompt": request.prompt,
               "system": request.system_prompt,
               "format": "json" if request.json_mode else None,
               "stream": False,
           })
           response.raise_for_status()
           return response.json()["response"]
   ```

2. Add settings in `core/config.py` (`ollama_base_url`, `ollama_model`).
3. Register it in `build_services()` in `core/container.py`:
   `available["ollama"] = OllamaProvider(http, settings.ollama_base_url, settings.ollama_model)`.
4. Put it first in `.env`: `LLM_PROVIDER_ORDER=ollama,gemini,openai,groq`.

No service or frontend changes are needed.

---

## 4. Making video generation real

`core/services/video.py` is currently a simulation. Replace the bodies of:

- `generate_clip(image_url, prompt)`: call an image-to-video API (Luma, Runway, Kling) and return
  `VideoResult(url=<clip url>, status="completed")`.
- `compile(clip_urls, audio_url)`: download the clips, run FFmpeg (e.g. `concat` + audio overlay),
  upload the result and return `VideoResult(url=<final url>, status="success")`.

Add any new API keys to `Settings` and pass them in via `build_services()`. Long-running jobs
are best moved to a background task queue with a polling endpoint.

---

## 5. Frontend conventions

- **Never call `axios`/`fetch` from components.** Add a typed function to `src/services/api.ts`.
- Errors from the API are thrown as `ApiError` (`status`, `code`, `details`). Use
  `isRateLimitError(e)` for quota messages.
- Styling uses **Tailwind CSS v4**. The theme lives in `src/index.css` (`@theme`).
- Icons come from **lucide-react** and animations from **motion/react**.
- API keys must **never** go into the frontend. Put them in the root `.env` and read them via
  `core.config.Settings`.

---

## 6. Backend conventions

- Business logic goes in `core`. Routers should stay a few lines long.
- Raise `core.exceptions.*` for expected failures and never `HTTPException` from `core`.
- Read configuration only through `Settings`, never `os.environ`.
- Use the shared `httpx.AsyncClient` (injected via `build_services`) for outbound HTTP.
- Everything is `async`. Don't use blocking calls such as `requests` or `time.sleep` in services.
- Add docstrings to every public function and class, and type hints everywhere.

---

## 7. Useful commands

```bash
uvicorn fastapi_backend.main:app --reload --port 8000   # backend (dev)
python -m fastapi_backend                               # same, via __main__.py
pytest                                                  # backend tests
cd frontend && npm run dev                              # frontend (dev, port 3000)
cd frontend && npm run lint                             # TS type-check
cd frontend && npm run build                            # production build → frontend/dist
```

Happy coding! 🚀
