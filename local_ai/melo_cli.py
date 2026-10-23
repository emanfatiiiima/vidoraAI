"""
MeloTTS command-line wrapper. Runs with the Python of the separate MeloTTS venv
(``local_ai/.venv-melo``), because MeloTTS pins library versions that clash
with the main worker. Only stdlib + melo imports are allowed here.

    python melo_cli.py --text-file in.txt --out out.wav --speaker EN-US --speed 1.0
    python melo_cli.py --warmup        # download the model + NLTK data once
"""

from __future__ import annotations

import argparse
import sys


def _ensure_nltk_data() -> None:
    # g2p_en needs these; newer NLTK versions renamed the tagger with an "_eng" suffix.
    import nltk

    for package in ("averaged_perceptron_tagger", "averaged_perceptron_tagger_eng", "cmudict"):
        nltk.download(package, quiet=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file")
    parser.add_argument("--out")
    parser.add_argument("--speaker", default="EN-US")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()

    _ensure_nltk_data()
    from melo.api import TTS

    model = TTS(language="EN", device=args.device)
    if args.warmup:
        print("MeloTTS is ready. Speakers:", ", ".join(model.hps.data.spk2id))
        return 0

    speakers = model.hps.data.spk2id
    if args.speaker not in speakers:
        print(f"Unknown speaker {args.speaker}. Available: {', '.join(speakers)}", file=sys.stderr)
        return 2
    with open(args.text_file, encoding="utf-8") as f:
        text = f.read()
    model.tts_to_file(text, speakers[args.speaker], args.out, speed=args.speed, quiet=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
