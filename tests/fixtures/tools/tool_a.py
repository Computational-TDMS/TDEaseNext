#!/usr/bin/env python3
"""
Mock Tool A - 模拟质谱工作流第一步
无输入，输出 {sample}_a.txt，产生模拟日志。
输出包含 TOOL_A_SIGNATURE 供下游 B 验证读取成功。
"""
import argparse
import sys
import uuid
from pathlib import Path
from datetime import datetime

# 下游 B 必须能读取到的签名，用于验证真正读到文件
SIGNATURE_KEY = "TOOL_A_SIGNATURE"


def main():
    parser = argparse.ArgumentParser(description="Tool A: 生成初始数据")
    parser.add_argument("-i", "--input", action="append", help="输入文件（本工具无输入）")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径，如 {sample}_a.txt")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sig = str(uuid.uuid4())
    log_lines = [
        f"[{datetime.now().isoformat()}] Tool A started",
        f"[{datetime.now().isoformat()}] Output path: {out_path}",
        f"[{datetime.now().isoformat()}] Signature: {SIGNATURE_KEY}={sig}",
        f"[{datetime.now().isoformat()}] Tool A completed successfully",
    ]
    for line in log_lines:
        print(line, file=sys.stderr)

    content = (
        f"# Tool A output\n"
        f"# Generated at {datetime.now().isoformat()}\n"
        f"# Step: A -> B\n"
        f"{SIGNATURE_KEY}={sig}\n"
    )
    out_path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
