#!/usr/bin/env python3
"""Mock tool that records argv for positional/flag assertions."""
import json
import sys
from pathlib import Path


def _extract_value(argv: list[str], flag: str, default: str = "") -> str:
    if flag not in argv:
        return default
    idx = argv.index(flag)
    if idx + 1 >= len(argv):
        return default
    return argv[idx + 1]


def main() -> int:
    argv = sys.argv[1:]
    capture_path = _extract_value(argv, "--capture-path", "echo_cmdline.json")
    payload = {"argv": argv}

    out_file = Path(capture_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print(f"ECHO_ARGV_JSON={json.dumps(payload, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
