"""
Local AI for VidoraAI.

* ``catalog``  - pure data, shared with the main backend (no heavy imports).
* everything else is the GPU worker, which runs in its own venv with PyTorch:
  start it with ``python -m local_ai`` and download models with
  ``python -m local_ai.download``. See LOCAL_SETUP.md in the project root.
"""
