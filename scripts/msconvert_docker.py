#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


def build_msconvert_command(input_path: str, output_path: str, params: dict) -> list[str]:
    cwd = os.getcwd()
    image = params.get("docker_image", "pwiz-skyline-i-agree-to-the-vendor-licenses:latest")
    container_mount = params.get("container_mount", "/data")
    # Map host cwd to container mount
    volume = f"{cwd}:{container_mount}"
    # Inside container paths
    in_name = Path(input_path).name
    out_name = Path(output_path).name
    in_container = f"{container_mount}/{in_name}"
    out_dir_container = container_mount
    
    # Note: We run container as root because Wine needs specific permissions
    # We'll fix file permissions after the container runs
    cmd = [
        "docker", "run", "--rm",
        "-v", volume,
        image,
        "wine", "msconvert",
        in_container,
        "-o", out_dir_container,
        "--outfile", out_name,
    ]
    
    # format flags
    fmt = params.get("format", "mzML").lower()
    if fmt == "mzml":
        cmd.append("--mzML")
    elif fmt == "mzxml":
        cmd.append("--mzXML")
    elif fmt == "mgf":
        cmd.append("--mgf")
    elif fmt == "mz5":
        cmd.append("--mz5")
    elif fmt == "mzmlb":
        cmd.append("--mzMLb")
    elif fmt == "text":
        cmd.append("--text")
    elif fmt == "ms1":
        cmd.append("--ms1")
    elif fmt == "cms1":
        cmd.append("--cms1")
    elif fmt == "ms2":
        cmd.append("--ms2")
    elif fmt == "cms2":
        cmd.append("--cms2")
    
    # extension override
    ext = params.get("extension")
    if ext:
        cmd += ["-e", str(ext)]
    
    # precision flags
    default_prec = params.get("default_precision", "64")
    if default_prec == "32":
        cmd.append("--32")
    else:
        cmd.append("--64")
    
    mz_prec = str(params.get("mz_precision", "64"))
    if mz_prec == "32":
        cmd.append("--mz32")
    else:
        cmd.append("--mz64")
    
    inten_prec = str(params.get("intensity_precision", "32"))
    if inten_prec == "64":
        cmd.append("--inten64")
    else:
        cmd.append("--inten32")
    
    # truncation options
    mz_trunc = params.get("mz_truncation")
    if mz_trunc is not None:
        cmd += ["--mzTruncation", str(mz_trunc)]
    
    inten_trunc = params.get("intensity_truncation")
    if inten_trunc is not None:
        cmd += ["--intenTruncation", str(inten_trunc)]
    
    # prediction options
    if params.get("mz_delta", False):
        cmd.append("--mzDelta")
    if params.get("intensity_delta", False):
        cmd.append("--intenDelta")
    if params.get("mz_linear", False):
        cmd.append("--mzLinear")
    if params.get("intensity_linear", False):
        cmd.append("--intenLinear")
    
    # compression options
    if params.get("gzip", False):
        cmd.append("--gzip")
    
    zlib = params.get("zlib")
    if zlib is not None:
        if zlib is False or zlib == "off":
            cmd.append("--zlib=off")
        else:
            cmd.append("--zlib")
    
    # numpress compression
    numpress_linear = params.get("numpress_linear")
    if numpress_linear is not None:
        if numpress_linear is True:
            cmd.append("--numpressLinear")
        else:
            cmd += ["--numpressLinear", str(numpress_linear)]
    
    numpress_linear_abstol = params.get("numpress_linear_abstol")
    if numpress_linear_abstol is not None:
        cmd += ["--numpressLinearAbsTol", str(numpress_linear_abstol)]
    
    if params.get("numpress_pic", False):
        cmd.append("--numpressPic")
    
    numpress_slof = params.get("numpress_slof")
    if numpress_slof is not None:
        if numpress_slof is True:
            cmd.append("--numpressSlof")
        else:
            cmd += ["--numpressSlof", str(numpress_slof)]
    
    if params.get("numpress_all", False):
        cmd.append("--numpressAll")
    
    # mzMLb specific options
    mzmlb_chunk_size = params.get("mzmlb_chunk_size")
    if mzmlb_chunk_size is not None:
        cmd += ["--mzMLbChunkSize", str(mzmlb_chunk_size)]
    
    mzmlb_compression_level = params.get("mzmlb_compression_level")
    if mzmlb_compression_level is not None:
        cmd += ["--mzMLbCompressionLevel", str(mzmlb_compression_level)]
    
    # other options
    if params.get("verbose", False):
        cmd.append("--verbose")
    
    if params.get("noindex", False):
        cmd.append("--noindex")
    
    contact_info = params.get("contact_info")
    if contact_info:
        contact_info_container = f"{container_mount}/{Path(contact_info).name}"
        cmd += ["-i", contact_info_container]
    
    if params.get("merge", False):
        cmd.append("--merge")
    
    if params.get("sim_as_spectra", False):
        cmd.append("--simAsSpectra")
    
    if params.get("srm_as_spectra", False):
        cmd.append("--srmAsSpectra")
    
    if params.get("combine_ion_mobility_spectra", False):
        cmd.append("--combineIonMobilitySpectra")
    
    if params.get("dda_processing", False):
        cmd.append("--ddaProcessing")
    
    if params.get("ignore_calibration_scans", False):
        cmd.append("--ignoreCalibrationScans")
    
    if params.get("accept_zero_length_spectra", False):
        cmd.append("--acceptZeroLengthSpectra")
    
    if params.get("ignore_missing_zero_samples", False):
        cmd.append("--ignoreMissingZeroSamples")
    
    if params.get("ignore_unknown_instrument_error", False):
        cmd.append("--ignoreUnknownInstrumentError")
    
    if params.get("strip_location_from_source_files", False):
        cmd.append("--stripLocationFromSourceFiles")
    
    if params.get("strip_version_from_software", False):
        cmd.append("--stripVersionFromSoftware")
    
    single_threaded = params.get("single_threaded")
    if single_threaded is not None:
        if single_threaded is True:
            cmd.append("--singleThreaded")
        else:
            cmd += ["--singleThreaded", str(single_threaded)]
    
    if params.get("continue_on_error", False):
        cmd.append("--continueOnError")
    
    run_index_set = params.get("run_index_set")
    if run_index_set:
        cmd += ["--runIndexSet", str(run_index_set)]
    
    # filters: list of strings or single string
    filters = params.get("filters")
    if filters:
        if isinstance(filters, (list, tuple)):
            for f in filters:
                cmd += ["--filter", str(f)]
        else:
            cmd += ["--filter", str(filters)]
    
    # chromatogram filters
    chromatogram_filters = params.get("chromatogram_filters")
    if chromatogram_filters:
        if isinstance(chromatogram_filters, (list, tuple)):
            for f in chromatogram_filters:
                cmd += ["--chromatogramFilter", str(f)]
        else:
            cmd += ["--chromatogramFilter", str(chromatogram_filters)]
    
    # config file
    config_file = params.get("config_file")
    if config_file:
        config_file_container = f"{container_mount}/{Path(config_file).name}"
        cmd += ["-c", config_file_container]
    
    # additional raw flags passthrough
    extra = params.get("extra_flags")
    if extra:
        if isinstance(extra, (list, tuple)):
            cmd += list(map(str, extra))
        else:
            cmd += shlex.split(str(extra))
    
    return cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, nargs="+")
    # Support both --output and -o
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", nargs="+")
    group.add_argument("-o", dest="output", nargs="+")
    ap.add_argument("--params", required=False, default="{}")
    ap.add_argument("--params-file", required=False, help="Path to JSON file with params (overrides --params)")
    args = ap.parse_args()

    # Debug logging
    print(f"[DEBUG] msconvert_docker started", file=sys.stderr)
    print(f"[DEBUG] Input: {args.input}", file=sys.stderr)
    print(f"[DEBUG] Output: {args.output}", file=sys.stderr)
    print(f"[DEBUG] Current directory: {os.getcwd()}", file=sys.stderr)
    try:
        print(f"[DEBUG] User ID: {os.getuid()}, Group ID: {os.getgid()}", file=sys.stderr)
    except AttributeError:
        pass  # Windows has no getuid/getgid

    # Only support one-to-one for now
    inp = args.input[0]
    outp = args.output[0]
    params = {}
    if getattr(args, "params_file", None):
        try:
            with open(args.params_file, "r", encoding="utf-8") as f:
                params = json.load(f)
            print(f"[DEBUG] Params loaded from file: {args.params_file}", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] Failed to read params file: {e}", file=sys.stderr)
    else:
        try:
            params = json.loads(args.params) if args.params else {}
            print(f"[DEBUG] Params: {params}", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] Failed to parse params: {e}", file=sys.stderr)

    cmd = build_msconvert_command(inp, outp, params)
    # Reuse image/mount info for post-fix
    image = params.get("docker_image", "pwiz-skyline-i-agree-to-the-vendor-licenses:latest")
    container_mount = params.get("container_mount", "/data")
    volume = f"{os.getcwd()}:{container_mount}"
    out_in_container = f"{container_mount}/{Path(outp).name}"
    print(f"[DEBUG] Docker command: {' '.join(cmd)}", file=sys.stderr)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[DEBUG] Command completed successfully", file=sys.stderr)
        print(f"[DEBUG] stdout: {result.stdout[:200]}...", file=sys.stderr)
        print(f"[DEBUG] stderr: {result.stderr[:200]}...", file=sys.stderr)

        # Fix file permissions after Docker container runs (container runs as root)
        output_file = Path(outp)
        if output_file.exists():
            uid = os.getuid()
            gid = os.getgid()
            chown_cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                volume,
                image,
                "chown",
                f"{uid}:{gid}",
                out_in_container,
            ]
            chmod_cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                volume,
                image,
                "chmod",
                "664",
                out_in_container,
            ]
            try:
                subprocess.run(chown_cmd, check=True, capture_output=True, text=True)
                subprocess.run(chmod_cmd, check=True, capture_output=True, text=True)
                print(
                    f"[DEBUG] Fixed permissions via docker for {output_file}: uid={uid}, gid={gid}",
                    file=sys.stderr,
                )
            except Exception as e:
                print(
                    f"[WARNING] Could not fix permissions for {output_file} via docker: {e}",
                    file=sys.stderr,
                )
                # Best-effort local chmod/chown (may fail if not owner)
                try:
                    output_file.chmod(0o664)
                except Exception:
                    pass

        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}", file=sys.stderr)
        print(f"[ERROR] stdout: {e.stdout[:500] if e.stdout else 'None'}", file=sys.stderr)
        print(f"[ERROR] stderr: {e.stderr[:500] if e.stderr else 'None'}", file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()

