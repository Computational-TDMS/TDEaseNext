#!/usr/bin/env python3
"""Mock source tool that writes a single output file to --out path."""
import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock source tool")
    parser.add_argument("--out", required=True, help="Output file path")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(f"mock-source-output: {out_path.name}\n", encoding="utf-8")
    print(f"MOCK_SOURCE_OUT={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
