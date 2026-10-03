"""
Image provider clients.

Each module here knows how to talk to exactly one image-generation API and
nothing else (no fallback, no data-URI conversion, no HTTP error mapping for
the web layer). :class:`core.services.ImageService` decides which client to
use for a request.
"""

from core.images.leonardo import LeonardoClient

__all__ = ["LeonardoClient"]
