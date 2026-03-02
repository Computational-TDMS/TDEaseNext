#!/usr/bin/env python3
"""
Mock Tool B - 模拟质谱工作流第二步
读取 A 的输出 (*_a.txt)，输出 {sample}_b.txt，产生模拟日志。
必须验证输入文件包含 TOOL_A_SIGNATURE 才继续，否则退出码非 0。
"""
import argparse
import sys
import uuid
from pathlib import Path
from datetime import datetime

# 必须从 A 的输出中读取到的签名，用于验证真正读到文件
EXPECTED_SIGNATURE_KEY = "TOOL_A_SIGNATURE"
OUTPUT_SIGNATURE_KEY = "TOOL_B_SIGNATURE"


def main():
    parser = argparse.ArgumentParser(description="Tool B: 处理 Tool A 的输出")
    parser.add_argument("-i", "--input", action="append", required=True, help="输入文件 (来自 Tool A)")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径，如 {sample}_b.txt")
    args = parser.parse_args()

    in_paths = args.input or []
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log_lines = [
        f"[{datetime.now().isoformat()}] Tool B started",
        f"[{datetime.now().isoformat()}] Input(s): {in_paths}",
        f"[{datetime.now().isoformat()}] Output path: {out_path}",
    ]

    content_parts = ["# Tool B output\n", f"# Generated at {datetime.now().isoformat()}\n", "# Step: B -> C\n"]
    validation_ok = False
    for inp in in_paths:
        p = Path(inp)
        if not p.exists():
            log_lines.append(f"[{datetime.now().isoformat()}] ERROR: Input not found: {inp}")
            print("\n".join(log_lines), file=sys.stderr)
            return 1
        text = p.read_text(encoding="utf-8")
        if EXPECTED_SIGNATURE_KEY not in text:
            log_lines.append(
                f"[{datetime.now().isoformat()}] ERROR: Input validation failed - "
                f"expected '{EXPECTED_SIGNATURE_KEY}' in {inp}, got content (first 200 chars): {repr(text[:200])}"
            )
            print("\n".join(log_lines), file=sys.stderr)
            return 1
        validation_ok = True
        content_parts.append(f"# Read from: {inp} [verified {EXPECTED_SIGNATURE_KEY} present]\n")
        content_parts.append(text)
        content_parts.append("\n")

    if not validation_ok:
        log_lines.append(f"[{datetime.now().isoformat()}] ERROR: No valid input file with {EXPECTED_SIGNATURE_KEY}")
        print("\n".join(log_lines), file=sys.stderr)
        return 1

    sig = str(uuid.uuid4())
    content_parts.append(f"{OUTPUT_SIGNATURE_KEY}={sig}\n")
    log_lines.append(f"[{datetime.now().isoformat()}] Input validation OK, wrote {OUTPUT_SIGNATURE_KEY}={sig}")
    log_lines.append(f"[{datetime.now().isoformat()}] Tool B completed successfully")
    for line in log_lines:
        print(line, file=sys.stderr)

    out_path.write_text("".join(content_parts), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
