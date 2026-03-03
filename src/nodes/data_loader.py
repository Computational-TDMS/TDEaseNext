#!/usr/bin/env python3
"""
传入数据节点

将原始输入文件复制到工作空间的 input_files/ 目录
"""
import argparse
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any


def load_data(
    workspace_dir: str,
    input_sources: List[str],
    copy_strategy: str = "copy",
    sample_name: str = None,
) -> Dict[str, Any]:
    """
    将输入文件复制到工作空间根目录（扁平结构，无子目录）

    Args:
        workspace_dir: 工作空间目录
        input_sources: 输入文件源路径列表
        copy_strategy: 复制策略 ("copy" 或 "link"，默认 "copy")
        sample_name: 目标文件名称（不含扩展名，必需参数）

    Returns:
        包含复制文件信息的字典
    """
    if not sample_name:
        raise ValueError("sample_name 是必需参数，请由 flowengine 指定目标文件名")

    workspace_path = Path(workspace_dir)

    # 创建工作空间目录（如果不存在）
    workspace_path.mkdir(parents=True, exist_ok=True)

    copied_files = []

    # 复制或链接输入文件到工作空间根目录
    for source_path in input_sources:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"输入文件不存在: {source_path}")

        # 目标文件名由 flowengine 通过 sample_name 参数指定
        target = workspace_path / f"{sample_name}{source.suffix}"
        
        if copy_strategy == "link":
            # 创建符号链接
            if target.exists():
                target.unlink()
            target.symlink_to(source.absolute())
        else:
            # 复制文件
            shutil.copy2(source, target)
        
        copied_files.append({
            "source": str(source),
            "target": str(target),
            "basename": sample_name
        })
    
    return {
        "workspace_dir": str(workspace_path),
        "copied_files": copied_files
    }


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="传入数据节点 - 复制输入文件到工作空间")
    parser.add_argument("--input", action="append", required=True,
                       help="输入文件路径（可多次使用）")
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
    sample_name = params.get("sample_name")
    
    # 复制输入文件到工作空间
    result = load_data(
        workspace_dir=args.output,
        input_sources=args.input,
        copy_strategy=copy_strategy,
        sample_name=sample_name
    )
    
    # 输出结果（用于 Snakemake）
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()