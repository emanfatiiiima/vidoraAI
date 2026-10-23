"""
Storage for media produced locally (narration, clips, final videos).

Files live under ``Settings.media_dir`` and are served by FastAPI at
``/api/media/...``, so the browser can play them and the URL survives page
reloads. :meth:`MediaStore.read` turns any media URL the app deals with
(local media URL, ``data:`` URI or http(s) link) back into bytes.
"""

from __future__ import annotations

import base64
import re
import uuid
from pathlib import Path

import httpx

from core.utils import fetch_bytes

URL_PREFIX = "/api/media/"
_DATA_URI_RE = re.compile(r"^data:(?P<mime>[\w/+.-]+)?(?:;[\w=-]+)*;base64,(?P<data>.*)$", re.DOTALL)
_CONTENT_TYPES = {
    ".wav": "audio/wav", ".mp3": "audio/mpeg", ".mp4": "video/mp4",
    ".png": "image/png", ".jpg": "image/jpeg", ".mlt": "application/xml",
}


class MediaStore:
    def __init__(self, root: Path, http: httpx.AsyncClient) -> None:
        self.root = root.resolve()
        self._http = http

    def new_file(self, folder: str, suffix: str) -> tuple[Path, str]:
        """A fresh, unique ``(path, url)`` pair in ``folder`` (the folder is created)."""
        name = f"{uuid.uuid4().hex[:16]}{suffix}"
        directory = self.root / folder
        directory.mkdir(parents=True, exist_ok=True)
        return directory / name, f"{URL_PREFIX}{folder}/{name}"

    def save(self, content: bytes, folder: str, suffix: str) -> str:
        """Store ``content`` and return its URL."""
        path, url = self.new_file(folder, suffix)
        path.write_bytes(content)
        return url

    def path_for(self, url: str) -> Path | None:
        """The file behind a local media URL, or ``None`` if ``url`` isn't one (or escapes the root)."""
        if not url.startswith(URL_PREFIX):
            return None
        path = (self.root / url[len(URL_PREFIX):].split("?")[0]).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            return None
        return path

    async def read(self, url: str) -> tuple[bytes, str | None]:
        """``(content, content_type)`` for a local media URL, ``data:`` URI or http(s) URL."""
        local = self.path_for(url)
        if local is not None:
            return local.read_bytes(), _CONTENT_TYPES.get(local.suffix.lower())
        if url.startswith("data:"):
            match = _DATA_URI_RE.match(url)
            if not match:
                raise ValueError("Unsupported data URI")
            return base64.b64decode(match.group("data")), match.group("mime")
        return await fetch_bytes(self._http, url)

    async def to_file(self, url: str, folder: str, default_suffix: str) -> Path:
        """A local file for ``url`` (downloaded/decoded into ``folder`` when needed)."""
        local = self.path_for(url)
        if local is not None:
            return local
        content, content_type = await self.read(url)
        suffix = next((s for s, t in _CONTENT_TYPES.items() if t == content_type), default_suffix)
        path, _ = self.new_file(folder, suffix)
        path.write_bytes(content)
        return path
