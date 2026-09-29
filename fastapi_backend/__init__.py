"""
VidoraAI FastAPI backend - the HTTP layer on top of ``core``.

- ``main.py``         : app factory, middleware, static frontend hosting
- ``routers/``        : endpoints grouped by feature
- ``schemas.py``      : request/response models (camelCase JSON)
- ``dependencies.py`` : dependency injection helpers
- ``errors.py``       : core exception -> HTTP response mapping
"""
