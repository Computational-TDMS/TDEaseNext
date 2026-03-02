#!/usr/bin/env python3
"""
FASTA 文件加载节点

将 FASTA 文件复制到工作空间根目录（扁平结构）
"""
import argparse
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any


def load_fasta(
    workspace_dir: str,
    fasta_file: str,
    copy_strategy: str = "copy"
) -> Dict[str, Any]:
    """
    将 FASTA 文件复制到工作空间根目录（扁平结构，无子目录）
    
    Args:
        workspace_dir: 工作空间目录
        fasta_file: FASTA 文件源路径
        copy_strategy: 复制策略 ("copy" 或 "link"，默认 "copy")
    
    Returns:
        包含复制文件信息的字典
    """
    workspace_path = Path(workspace_dir)
    
    # 创建工作空间目录（如果不存在）
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    source = Path(fasta_file)
    if not source.exists():
        raise FileNotFoundError(f"FASTA 文件不存在: {fasta_file}")
    
    # 目标文件：直接在工作空间根目录，保留原始文件名
    target = workspace_path / source.name
    
    if copy_strategy == "link":
        # 创建符号链接
        if target.exists():
            target.unlink()
        target.symlink_to(source.absolute())
    else:
        # 复制文件
        shutil.copy2(source, target)
    
    return {
        "workspace_dir": str(workspace_path),
        "fasta_file": {
            "source": str(source),
            "target": str(target),
            "basename": source.stem
        }
    }


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="FASTA 文件加载节点 - 复制 FASTA 文件到工作空间")
    parser.add_argument("--fasta", required=True,
                       help="FASTA 文件路径")
    parser.add_argument("--output", required=True,
                       help="输出目录路径（工作空间目录）")
    parser.add_argument("--params", type=str, default="{}",
                       help="JSON 格式的参数（可选：copy_strategy）")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 解析参数
    try:
        params = json.loads(args.params) if args.params else {}
    except json.JSONDecodeError:
        params = {}
    
    copy_strategy = params.get("copy_strategy", "copy")
    
    # 复制 FASTA 文件到工作空间
    result = load_fasta(
        workspace_dir=args.output,
        fasta_file=args.fasta,
        copy_strategy=copy_strategy
    )
    
    # 输出结果（用于 Snakemake）
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

