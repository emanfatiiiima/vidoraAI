"""
Download local models ahead of time (so the first video doesn't stall on a
multi-GB download) and mark them as ready for the popup.

    python -m local_ai.download --list            # every engine, its size and status
    python -m local_ai.download kokoro sdxl-turbo ltx-video
    python -m local_ai.download recommended       # kokoro + piper + sdxl-turbo + ltx-video
    python -m local_ai.download all               # everything (~110 GB)

Run it with the worker venv. Downloads resume if interrupted - just run it again.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from local_ai import catalog
from local_ai.runtime import MELO_PYTHON, PACKAGE_DIR, is_ready, mark_ready

RECOMMENDED = ("kokoro", "piper", "sdxl-turbo", "ltx-video")


def download(engine_id: str) -> None:
    from huggingface_hub import hf_hub_download, snapshot_download

    engine = catalog.ENGINES[engine_id]
    print(f"\n=== {engine.label} ({engine_id}, ~{engine.size}) ===")
    for item in engine.downloads:
        if item.filename:
            print(f"  - {item.repo}/{item.filename}")
            hf_hub_download(item.repo, item.filename)
        else:
            print(f"  - {item.repo}")
            snapshot_download(item.repo, allow_patterns=list(item.allow) if item.allow else None)

    # Engines that fetch their files through their own library.
    if engine_id == "kokoro":
        _ensure_spacy_model()
    elif engine_id == "xtts":
        _download_xtts()
    elif engine_id == "melo":
        _download_melo()

    mark_ready(engine_id)
    print(f"  OK - {engine.label} is ready.")


def _ensure_spacy_model() -> None:
    # Kokoro's English phonemizer (misaki) needs this spaCy model; installing it
    # now avoids a pip call in the middle of the first narration.
    import importlib.util

    if importlib.util.find_spec("en_core_web_sm") is None:
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)


def _download_xtts() -> None:
    if os.environ.get("COQUI_TOS_AGREED") != "1":
        sys.exit(
            "XTTS-v2 is licensed under the Coqui Public Model License (non-commercial).\n"
            "Read https://coqui.ai/cpml and, if you agree, set COQUI_TOS_AGREED=1 and run this again."
        )
    from TTS.utils.manage import ModelManager

    ModelManager().download_model("tts_models/multilingual/multi-dataset/xtts_v2")


def _download_melo() -> None:
    if not MELO_PYTHON.is_file():
        sys.exit(f"MeloTTS venv not found at {MELO_PYTHON}. Create it first (LOCAL_SETUP.md, step 6).")
    subprocess.run([str(MELO_PYTHON), "-m", "unidic", "download"], check=True)
    subprocess.run([str(MELO_PYTHON), str(PACKAGE_DIR / "melo_cli.py"), "--warmup", "--device", "cpu"], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engines", nargs="*", help="engine ids, 'recommended' or 'all'")
    parser.add_argument("--list", action="store_true", help="show every engine and whether it is downloaded")
    args = parser.parse_args()

    if args.list or not args.engines:
        for kind, title in (("tts", "Text to speech"), ("image", "Text to image"), ("video", "Image to video")):
            print(f"\n{title}:")
            for engine_id in catalog.engine_ids(kind):
                engine = catalog.ENGINES[engine_id]
                state = "ready" if is_ready(engine_id) else "not downloaded"
                print(f"  {engine_id:<14} {engine.size:<28} {state:<15} {engine.note}")
        return 0

    wanted: list[str] = []
    for name in args.engines:
        if name == "all":
            wanted += list(catalog.ENGINES)
        elif name == "recommended":
            wanted += list(RECOMMENDED)
        elif name in catalog.ENGINES:
            wanted.append(name)
        else:
            print(f"Unknown engine '{name}'. Use --list to see the ids.")
            return 2

    failed = []
    for engine_id in dict.fromkeys(wanted):  # keep order, drop duplicates
        try:
            download(engine_id)
        except SystemExit as exc:
            print(f"  SKIPPED - {exc}")
            failed.append(engine_id)
        except Exception as exc:  # noqa: BLE001 - keep going with the other engines
            print(f"  FAILED - {exc}")
            if "401" in str(exc) or "gated" in str(exc).lower():
                print("  This model is gated: open its page on huggingface.co, click 'Agree and access',\n"
                      "  then run `hf auth login` with a READ token and try again.")
            failed.append(engine_id)

    if failed:
        print(f"\nNot ready: {', '.join(failed)}")
        return 1
    print("\nAll requested models are ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
