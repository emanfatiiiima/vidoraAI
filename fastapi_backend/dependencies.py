"""
FastAPI dependencies.

Route handlers receive services through ``Depends(get_services)`` rather than
importing globals. In tests you can swap them with::

    app.dependency_overrides[get_services] = lambda: fake_services
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from core import Services


def get_services(request: Request) -> Services:
    """Return the :class:`core.Services` bundle created at application startup."""
    return request.app.state.services


#: Shorthand type for route parameters: ``services: ServicesDep``.
ServicesDep = Annotated[Services, Depends(get_services)]
