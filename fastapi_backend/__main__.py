"""
Allow ``python -m fastapi_backend`` as a shortcut for running the dev server.

Environment variables ``HOST``, ``PORT`` and ``RELOAD`` can override defaults.
"""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_backend.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )
