#!/usr/bin/env python3
"""CLI entrypoint for `prsm_bundle_builder` tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.services.prsm_bundle_builder import build_prsm_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build TopMSV PrSM bundle tables")
    parser.add_argument("--prsm-single", required=True, help="Path to TopPIC *_prsm_single.tsv")
    parser.add_argument("--ms2-msalign", required=True, help="Path to TopFD *_ms2.msalign")
    parser.add_argument("--output-dir", required=True, help="Directory for prsm_table_clean.tsv and prsm_bundle.tsv")
    parser.add_argument("--ms2-feature", required=False, help="Optional TopFD *_ms2.feature path")
    parser.add_argument(
        "--ms2-topn",
        type=int,
        default=120,
        help="Top N peaks by intensity to keep for each spectrum (0 = keep all)",
    )
    args = parser.parse_args()

    stats = build_prsm_bundle(
        prsm_single_path=Path(args.prsm_single),
        ms2_msalign_path=Path(args.ms2_msalign),
        output_dir=Path(args.output_dir),
        ms2_topn=args.ms2_topn,
        ms2_feature_path=Path(args.ms2_feature) if args.ms2_feature else None,
    )
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

