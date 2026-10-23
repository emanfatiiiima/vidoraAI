"""
API routers, grouped by feature. All are mounted under ``/api`` in ``main.py``.

| Router        | Endpoints                                                       |
|---------------|-----------------------------------------------------------------|
| health        | GET  /health                                                    |
| generation    | POST /generate                                                  |
| topics        | POST /topics/{basic,unique,trending}, GET /trends, GET /news    |
| scripts       | POST /script, /script/summary, /script/export                   |
| scenes        | POST /scenes/split, /scenes/prompt                              |
| ai_options    | GET /ai-options, POST /ai-options/verify                        |
| media         | POST /tts, GET /tts/voices, POST /generate-image,               |
|               | POST /generate-video, POST /compile-video                       |
| export        | POST /export/project (ZIP of the whole project)                 |
"""

from fastapi import APIRouter

from fastapi_backend.routers import ai_options, export, generation, health, media, scenes, scripts, topics

api_router = APIRouter(prefix="/api")
for _module in (health, ai_options, generation, topics, scripts, scenes, media, export):
    api_router.include_router(_module.router)

__all__ = ["api_router"]
