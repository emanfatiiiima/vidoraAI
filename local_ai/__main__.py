"""Start the local GPU worker: ``python -m local_ai`` (from the project root)."""

import logging

import uvicorn

from local_ai.runtime import HOST, PORT

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    uvicorn.run("local_ai.server:app", host=HOST, port=PORT, log_level="info")
