"""
工具注册表 - 管理所有可用工具的元信息

目前先设计为python版本
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import json



class ToolRegistry:
    """
    工具注册表
    
    用于管理工具的元信息：
    - 脚本路径
    - 输入参数定义
    - 输出模式
    - Conda 环境
    - 默认参数
    """
    
    def __init__(self, registry_file: Optional[str] = None):
        """
        初始化注册表
        
        Args:
            registry_file: 注册表 JSON 文件路径（可选）
                           如果为 None，默认从 config/tools_registry.json 加载
        """
        self.registry: Dict[str, Dict[str, Any]] = {}
        
        # 确定注册表文件路径
        if registry_file is None:
            # 默认从项目根目录的 config/tools_registry.json 加载
            project_root = Path(__file__).parent.parent.parent
            default_registry_file = project_root / "config" / "tools_registry.json"
            if default_registry_file.exists():
                registry_file = str(default_registry_file)
        
        # 如果提供了注册表文件，加载它
        if registry_file and Path(registry_file).exists():
            self.load_from_file(registry_file)
        else:
            # 如果没有找到配置文件，加载默认注册表（向后兼容）
            self._load_default_registry()

        # 额外加载分文件的工具定义（config/tools/*.json），并与已有注册表合并
        tools_dir = Path(__file__).parent.parent.parent / "config" / "tools"
        if tools_dir.exists() and tools_dir.is_dir():
            for tool_json in tools_dir.glob("*.json"):
                try:
                    with open(tool_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            # 检查是否为嵌套结构 { "tool_id": { ... } }
                            # 简单的启发式：如果文件名作为键存在，且对应的值是字典
                            filename_stem = tool_json.stem
                            if filename_stem in data and isinstance(data[filename_stem], dict):
                                self.registry.update(data)
                            # 检查是否为扁平结构 { "id": "tool_id", ... }
                            elif "id" in data:
                                self.registry[data["id"]] = data
                            # 如果都没有，尝试使用文件名作为 ID
                            else:
                                self.registry[filename_stem] = data
                except Exception:
                    pass
    
    def _load_default_registry(self):
        """加载默认的工具注册表"""
        # 传入数据节点 - 复制输入文件到工作空间根目录（扁平结构）
        self.registry.update({
            "data_loader": {
                "tool_type": "script",
                "tool_path": "src/nodes/data_loader.py",
                "input_params": ["input_sources"],
                "input_param_flags": {"input_sources": "input"},  # 参数名到命令行标志的映射
                "output_patterns": [
                    {"pattern": "{sample}.mzML", "handle": "mzml"}
                ],
                "output_flag_supported": True,
                "param_mapping": {},
                "conda_env": None,
                "description": "传入数据节点 - 将原始输入文件（mzML）复制到工作空间根目录（扁平结构，无子目录）"
            },
            "fasta_loader": {
                "tool_type": "script",
                "tool_path": "src/nodes/fasta_loader.py",
                "input_params": ["fasta_file"],
                "input_param_flags": {"fasta_file": "fasta"},  # 参数名到命令行标志的映射
                "output_patterns": [
                    {"pattern": "{fasta_filename}.fasta", "handle": "fasta"}
                ],
                "output_flag_supported": True,
                "param_mapping": {},
                "conda_env": None,
                "description": "FASTA 文件加载节点 - 将 FASTA 文件复制到工作空间根目录（扁平结构，无子目录）"
            }
        })
        
        # TOPPIC 系列工具 - 命令行工具模式
        self.registry.update({
            "msconvert": {
                "tool_type": "command",  # 命令行工具
                "tool_path": "msconvert",  # 可执行文件名（需要在 PATH 中或完整路径）
                "input_params": ["input_files"],
                "output_patterns": [
                    {"pattern": "{sample}.mzML", "handle": "mzml"}
                ],
                "output_flag": "-o",  # 输出目录标志
                "param_mapping": {
                    # 参数名到命令行标志的映射
                    "output_format": {"flag": "--mzML", "type": "choice"},  # 根据值选择不同的标志
                    "mz_precision": {"flag": "--mz32", "type": "choice"},  # 32 -> --mz32, 64 -> --mz64
                    "intensity_precision": {"flag": "--inten32", "type": "choice"},
                    "peak_picking_enabled": {"flag": "--filter", "type": "conditional"},
                },
                "conda_env": None,  # 如果工具在系统 PATH 中，不需要 conda
                "description": "MSConvert - 原始数据格式转换工具（ProteoWizard）"
            },
            "topfd": {
                "tool_type": "command",
                "tool_path": "topfd",
                "input_params": ["input_files", "mzml_files"],
                "output_patterns": [
                    {"pattern": "{sample}_ms2.msalign", "handle": "msalign"}
                ],
                # 扁平化工作空间：不需要复制，TopFD直接输出到工作目录
                "output_flag_supported": True,
                "param_mapping": {
                    "activation": {"flag": "-a", "short": True, "type": "value"},
                    "max_charge": {"flag": "-c", "short": True, "type": "value"},
                    "max_mass": {"flag": "-m", "short": True, "type": "value"},
                    "mz_error": {"flag": "-e", "short": True, "type": "value"},
                    "ms_one_sn_ratio": {"flag": "-r", "short": True, "type": "value"},
                    "ms_two_sn_ratio": {"flag": "-s", "short": True, "type": "value"},
                    "missing_level_one": {"flag": "-o", "short": True, "type": "boolean"},
                    "precursor_window": {"flag": "-w", "short": True, "type": "value"},
                    "msdeconv": {"flag": "-n", "short": True, "type": "boolean"},
                    "env_cnn_cutoff": {"flag": "-v", "short": True, "type": "value"},
                    "disable_frag_num_filtering": {"flag": "-d", "short": True, "type": "boolean"},
                    "ecscore_cutoff": {"flag": "-t", "short": True, "type": "value"},
                    "min_scan_number": {"flag": "-b", "short": True, "type": "value"},
                    "single_scan_noise": {"flag": "-i", "short": True, "type": "boolean"},
                    "disable_additional_feature_search": {"flag": "-f", "short": True, "type": "boolean"},
                    "split_intensity_ratio": {"flag": "-l", "short": True, "type": "value"},
                    "thread_number": {"flag": "-u", "short": True, "type": "value"},
                    "skip_html_folder": {"flag": "-g", "short": True, "type": "boolean"},
                },
                "conda_env": None,
                "description": "TopFD - 质谱去卷积工具"
            },
            "toppic": {
                "tool_type": "command",
                "tool_path": "toppic",
                "input_params": ["input_files", "msalign_files"],
                "output_patterns": [
                    {"pattern": "{sample}_ms2.toppic_raw_prsm", "handle": "prsm"}
                ],
                # toppic 需要 fasta_file 作为第一个位置参数
                "positional_params": ["fasta_file"],
                # 扁平化工作空间：不需要复制，TopPIC直接输出到工作目录
                "output_flag_supported": True,
                "param_mapping": {
                    "activation": {"flag": "-a", "short": True, "type": "value"},
                    "fixed_mod": {"flag": "-f", "short": True, "type": "value"},
                    "n_terminal_form": {"flag": "-n", "short": True, "type": "value"},
                    "proteoform_type": {"flag": "-R", "short": True, "type": "value"},
                    "num_shift": {"flag": "-s", "short": True, "type": "value"},
                    "min_shift": {"flag": "-m", "short": True, "type": "value"},
                    "max_shift": {"flag": "-M", "short": True, "type": "value"},
                    "variable_ptm_num": {"flag": "-S", "short": True, "type": "value"},
                    "variable_ptm_file_name": {"flag": "-b", "short": True, "type": "value"},
                    "decoy": {"flag": "-d", "short": True, "type": "boolean"},
                    "mass_error_tolerance": {"flag": "-e", "short": True, "type": "value"},
                    "proteoform_error_tolerance": {"flag": "-p", "short": True, "type": "value"},
                    "spectrum_cutoff_type": {"flag": "-t", "short": True, "type": "value"},
                    "spectrum_cutoff_value": {"flag": "-v", "short": True, "type": "value"},
                    "proteoform_cutoff_type": {"flag": "-T", "short": True, "type": "value"},
                    "proteoform_cutoff_value": {"flag": "-V", "short": True, "type": "value"},
                    "approximate_spectra": {"flag": "-A", "short": True, "type": "boolean"},
                    "lookup_table": {"flag": "-l", "short": True, "type": "boolean"},
                    "local_ptm_file_name": {"flag": "-B", "short": True, "type": "value"},
                    "miscore_threshold": {"flag": "-H", "short": True, "type": "value"},
                    "thread_number": {"flag": "-u", "short": True, "type": "value"},
                    "num_combined_spectra": {"flag": "-r", "short": True, "type": "value"},
                    "combined_file_name": {"flag": "-c", "short": True, "type": "value"},
                    "no_topfd_feature": {"flag": "-x", "short": True, "type": "boolean"},
                    "keep_temp_files": {"flag": "-k", "short": True, "type": "boolean"},
                    "keep_decoy_ids": {"flag": "-K", "short": True, "type": "boolean"},
                    "skip_html_folder": {"flag": "-g", "short": True, "type": "boolean"},
                },
                "conda_env": None,
                "description": "TopPIC - 蛋白形式识别工具"
            }
        })
    
    def load_from_file(self, registry_file: str):
        """
        从 JSON 文件加载注册表
        
        Args:
            registry_file: JSON 文件路径
        """
        with open(registry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 如果 JSON 文件是字典格式，直接更新
            if isinstance(data, dict):
                self.registry.update(data)
            else:
                raise ValueError(f"Invalid registry file format: expected dict, got {type(data)}")
    
    def save_to_file(self, registry_file: str):
        """
        保存注册表到 JSON 文件
        
        Args:
            registry_file: JSON 文件路径
        """
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def register_tool(
        self,
        tool_type: str,
        script_path: str,
        input_params: Optional[List[str]] = None,
        output_patterns: Optional[List[Dict[str, str]]] = None,
        conda_env: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        注册新工具
        
        Args:
            tool_type: 工具类型标识
            script_path: 脚本路径
            input_params: 输入参数名列表
            output_patterns: 输出文件模式
            conda_env: Conda 环境路径
            description: 工具描述
        """
        self.registry[tool_type] = {
            "script_path": script_path,
            "input_params": input_params or ["input_files"],
            "output_patterns": output_patterns or [{"pattern": "{sample}_output", "handle": "output"}],
            "conda_env": conda_env,
            "description": description or f"Tool: {tool_type}"
        }
    
    def get_tool_info(self, tool_type: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        Args:
            tool_type: 工具类型
            
        Returns:
            工具信息字典，如果不存在返回 None
        """
        return self.registry.get(tool_type)
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有注册的工具
        
        Returns:
            工具注册表字典
        """
        return self.registry.copy()
