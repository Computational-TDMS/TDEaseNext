#!/usr/bin/env python
"""
Spectrum summing CLI (Snakemake-friendly).

This script exposes a minimal interface so it can be called directly by the
generic ToolNode wrapper. Only the first input file is processed, and exactly
one output file must be provided. All configuration lives inside the JSON
payload passed through ``--params``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pyopenms


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spectrum summing tool")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input mzML/mzXML files (only the first entry is used).",
    )
    parser.add_argument(
        "--output",
        action="append",
        required=True,
        help="Output mzML file (exactly one expected).",
    )
    parser.add_argument(
        "--params",
        default="{}",
        help="JSON string with processing parameters.",
    )
    return parser.parse_args()


def load_params(raw: str) -> dict:
    defaults = {
        "method": "block",
        "block_size": 5,
        "start_scan": 1,
        "end_scan": 100,
        "ms_level": 1,
        "rt_tolerance": 10.0,
        "mz_tolerance": 0.001,
    }
    try:
        user_params = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse --params JSON: {exc}") from exc
    defaults.update(user_params)
    return defaults


def block_summing(exp, block_size, ms_level):
    print(f"Performing block summing with block size {block_size} for MS level {ms_level}")
    filtered_exp = pyopenms.MSExperiment()
    for spec in exp:
        if spec.getMSLevel() == ms_level:
            filtered_exp.addSpectrum(spec)
    if filtered_exp.size() == 0:
        print(f"No spectra found with MS level {ms_level}")
        return filtered_exp
    merger = pyopenms.SpectraMerger()
    params = merger.getParameters()
    params.setValue("block_method:rt_block_size", block_size)
    merger.setParameters(params)
    merger.mergeSpectraBlockWise(filtered_exp)
    return filtered_exp


def range_summing(exp, start_scan, end_scan, ms_level):
    print(f"Performing range summing from scan {start_scan} to {end_scan} for MS level {ms_level}")
    if start_scan > end_scan or start_scan < 1 or end_scan > exp.size() or end_scan < 1:
        raise ValueError("Invalid scan range")
    range_exp = pyopenms.MSExperiment()
    for scan_number, spectrum in enumerate(exp):
        if spectrum.getMSLevel() == ms_level and start_scan - 1 <= scan_number <= end_scan:
            range_exp.addSpectrum(spectrum)
    if range_exp.size() == 0:
        print(f"No spectra found with MS level {ms_level} in the specified range")
        return range_exp
    merger = pyopenms.SpectraMerger()
    params = merger.getParameters()
    params.setValue("block_method:rt_block_size", range_exp.size())
    merger.setParameters(params)
    merger.mergeSpectraBlockWise(range_exp)
    return range_exp


def precursor_summing(exp, ms_level, rt_tolerance, mz_tolerance):
    if ms_level != 2:
        raise ValueError("Precursor summing is only applicable to MS level 2")
    filtered_exp = pyopenms.MSExperiment()
    for spec in exp:
        if spec.getMSLevel() == ms_level:
            filtered_exp.addSpectrum(spec)
    if filtered_exp.size() == 0:
        print("No MS2 spectra found")
        return filtered_exp
    merger = pyopenms.SpectraMerger()
    params = merger.getParameters()
    params.setValue("precursor_method:rt_tolerance", rt_tolerance)
    params.setValue("precursor_method:mz_tolerance", mz_tolerance)
    merger.setParameters(params)
    merger.mergeSpectraPrecursors(filtered_exp)
    return filtered_exp


def save_results(summed_exp, output_path: str):
    if summed_exp.size() == 0:
        raise RuntimeError("No summed spectra to save")
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    pyopenms.MzMLFile().store(output_path, summed_exp)
    print(f"Saved {summed_exp.size()} spectra to {output_path}")


def main() -> int:
    args = parse_arguments()
    if not args.input:
        print("No --input provided", file=sys.stderr)
        return 2
    if not args.output or len(args.output) != 1:
        print("Exactly one --output must be provided", file=sys.stderr)
        return 2

    params = load_params(args.params)
    input_file = args.input[0]
    output_file = args.output[0]

    try:
        exp = pyopenms.MSExperiment()
        pyopenms.MzMLFile().load(input_file, exp)
        method = params["method"]
        ms_level = int(params.get("ms_level", 1))

        if method == "block":
            summed = block_summing(exp, int(params.get("block_size", 5)), ms_level)
        elif method == "range":
            summed = range_summing(
                exp,
                int(params.get("start_scan", 1)),
                int(params.get("end_scan", 100)),
                ms_level,
            )
        elif method == "precursor":
            summed = precursor_summing(
                exp,
                ms_level,
                float(params.get("rt_tolerance", 10.0)),
                float(params.get("mz_tolerance", 0.001)),
            )
        else:
            raise ValueError(f"Unsupported method '{method}'")

        save_results(summed, output_file)
        return 0
    except Exception as exc:
        print(f"Error during processing: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

