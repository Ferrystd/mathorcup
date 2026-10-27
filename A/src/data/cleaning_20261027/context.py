"""Shared guards for the frozen 2026-10-27 reproduction. Not a generic cleaner."""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_input(raw):
    expected = json.loads((HERE / "input_manifest.json").read_text(encoding="utf-8"))["sha256"]
    actual = {p.name: file_hash(p) for p in raw.iterdir() if p.is_file()}
    if actual != expected:
        raise ValueError("Input differs from the audited nine-file version; stop and re-audit.")
    return actual

def check_paths(raw, run, output):
    for left, right in [(raw, run), (raw, output), (run, output)]:
        if left == right or left.is_relative_to(right) or right.is_relative_to(left):
            raise ValueError("Input, run, and output directories must not overlap.")

def load_context():
    if sys.flags.optimize:
        raise RuntimeError("Do not use Python -O: verification assertions must remain enabled.")
    config = json.loads(Path(os.environ["MATHORCUP_CONTEXT"]).read_text(encoding="utf-8"))
    raw, run, output = (Path(config[k]).resolve() for k in ("input", "run", "output"))
    check_paths(raw, run, output)
    validate_input(raw)
    return raw, run, output
