"""
通用工具节点 - 所有工具节点的统一接口
每个节点只是工具的 Python 对接层，通过脚本调用实际工具
"""
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os


class ToolNode:
    """
    通用工具节点
    
    设计理念：
    - 不需要为每个工具定义专门的节点类
    - 只需要配置：输入、输出、参数、脚本路径
    - 实际执行通过 Snakemake 调用封装工具的脚本
    """
    
    def __init__(
        self,
        node_id: str,
        node_data: Dict[str, Any],
        platform: str = "linux",
        tool_registry: Optional[Dict[str, Any]] = None
    ):
        """
        初始化工具节点
        
        Args:
            node_id: 节点唯一标识
            node_data: 节点的 data 字段（包含 type, params 等）
            platform: 平台类型 ("linux" 或 "windows")
            tool_registry: 工具注册表（可选，用于查找脚本路径）
        """
        self.node_id = node_id
        self.node_data = node_data
        self.platform = platform
        self.params = node_data.get("params", {})
        self.node_type = node_data.get("type", "")
        self.tool_registry = tool_registry or {}
        # 工具类型（command 或 script）
        self.tool_type = self.params.get("tool_type")
        if not self.tool_type and self.node_type in self.tool_registry:
            self.tool_type = self.tool_registry[self.node_type].get("tool_type", "script")
        else:
            self.tool_type = self.tool_type or "script"
        
        # 从 params 或注册表获取工具路径/脚本路径
        self.script_path = self._resolve_script_path()
        
        # 输入参数映射：定义哪些参数名对应输入文件
        if "input_params" in self.params:
            self.input_params = self.params["input_params"]
        elif self.node_type in self.tool_registry:
            self.input_params = self.tool_registry[self.node_type].get("input_params", ["input_files"])
        else:
            self.input_params = ["input_files"]
        
        # 输出文件模式
        if "output_patterns" in self.params:
            self.output_patterns = self.params["output_patterns"]
        elif self.node_type in self.tool_registry:
            self.output_patterns = self.tool_registry[self.node_type].get("output_patterns", [])
        else:
            self.output_patterns = [{"pattern": "{input_basename}_output", "handle": "output"}]
        
        # 参数映射（从注册表获取）
        if "param_mapping" not in self.params and self.node_type in self.tool_registry:
            self.params["param_mapping"] = self.tool_registry[self.node_type].get("param_mapping", {})
    
    def _resolve_script_path(self) -> str:
        """
        解析工具路径（脚本路径或可执行文件路径）
        
        优先级：
        1. params 中的 tool_path 或 script_path
        2. 注册表中的 tool_path 或 script_path
        3. 基于 node_type 的默认路径
        
        Returns:
            工具路径
        """
        # 1. 直接从 params 获取
        tool_path = self.params.get("tool_path") or self.params.get("script_path")
        if tool_path:
            return self._normalize_path(tool_path)
        
        # 2. 从注册表获取
        if self.node_type in self.tool_registry:
            registry_entry = self.tool_registry[self.node_type]
            tool_path = registry_entry.get("tool_path") or registry_entry.get("script_path")
            if tool_path:
                return self._normalize_path(tool_path)
        
        # 3. 默认路径（基于 node_type）
        # 如果是命令行工具，使用工具名；如果是脚本，使用脚本路径
        default_path = self.node_type if self.tool_type == "command" else f"scripts/{self.node_type}.py"
        return self._normalize_path(default_path)
    
    def get_input_params(self) -> List[str]:
        """
        返回该节点接受的输入参数名列表
        
        Returns:
            输入参数名列表
        """
        return self.input_params
    
    def get_output_patterns(self) -> List[Dict[str, str]]:
        """
        返回输出文件模式
        
        Returns:
            输出模式列表，每个元素包含：
            - "pattern": 文件模式（如 "{input_basename}.mzML"）
            - "handle": 输出端口标识（如 "mzML", "msalign"）
        """
        return self.output_patterns
    
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """
        验证配置是否完整
        
        Returns:
            (是否有效, 错误信息)
        """
        # 检查脚本路径是否存在（如果提供的是绝对路径）
        if os.path.isabs(self.script_path) and not os.path.exists(self.script_path):
            return False, f"Script path does not exist: {self.script_path}"
        
        return True, None
    
    def generate_snakemake_rule(
        self,
        input_files: List[str],
        output_files: List[str],
        threads: int = 1,
        memory_mb: Optional[int] = None,
        log_file: Optional[str] = None,
        conda_env: Optional[str] = None,
        input_files_map: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        生成 Snakemake 规则字符串
        
        Args:
            input_files: 输入文件列表（Snakemake 格式）
            output_files: 输出文件列表（Snakemake 格式）
            threads: 线程数
            memory_mb: 内存需求（MB）
            log_file: 日志文件路径
            conda_env: Conda 环境路径（可选）
            input_files_map: 输入参数名到文件列表的映射（用于命名输入）
            
        Returns:
            Snakemake 规则字符串
        """
        # 构建规则
        rule_parts = [f"rule {self.node_id}:"]
        
        # 输入
        rule_parts.append("    input:")
        # 如果有多个输入参数，使用命名输入
        if input_files_map and len(input_files_map) > 1:
            for param_name, files in input_files_map.items():
                if files:
                    rule_parts.append(f'        {param_name}="{files[0]}",')
            if input_files_map:
                rule_parts[-1] = rule_parts[-1].rstrip(',')
        elif len(input_files) == 1:
            rule_parts.append(f'        "{input_files[0]}"')
        else:
            for inp in input_files:
                rule_parts.append(f'        "{inp}",')
            if input_files:
                rule_parts[-1] = rule_parts[-1].rstrip(',')
        
        # 输出
        rule_parts.append("    output:")
        if len(output_files) == 1:
            rule_parts.append(f'        "{output_files[0]}"')
        else:
            for out in output_files:
                rule_parts.append(f'        "{out}",')
            if output_files:
                rule_parts[-1] = rule_parts[-1].rstrip(',')
        
        # 参数（传递给脚本的参数）
        rule_parts.append("    params:")
        # 将 params 中的所有非文件参数传递给脚本
        skip_keys = ["script_path", "input_params", "output_patterns", "input_files", "output_dir",
                     "tool_type", "tool_path", "param_mapping", "positional_params", 
                     "output_flag_supported", "input_flag", "output_flag", "conda_env"]
        for key, value in self.params.items():
            if key not in skip_keys:
                if isinstance(value, str):
                    rule_parts.append(f'        {key}="{value}",')
                elif isinstance(value, (int, float)):
                    rule_parts.append(f'        {key}={value},')
                elif isinstance(value, bool):
                    rule_parts.append(f'        {key}={str(value).lower()},')
                else:
                    rule_parts.append(f'        {key}="{str(value)}",')
        if rule_parts[-1].endswith(','):
            rule_parts[-1] = rule_parts[-1].rstrip(',')
        
        # 线程和资源
        if threads > 1:
            rule_parts.append(f"    threads: {threads}")
        if memory_mb:
            rule_parts.append("    resources:")
            rule_parts.append(f"        mem_mb={memory_mb}")
        
        # Conda 环境
        if conda_env:
            rule_parts.append(f'    conda: "{conda_env}"')
        elif self.params.get("conda_env"):
            rule_parts.append(f'    conda: "{self.params["conda_env"]}"')
        
        # 日志（如果使用 samples，添加 {sample} 通配符）
        if log_file:
            if "{sample}" not in log_file and "{input_basename}" not in log_file:
                # 检查输出文件是否包含通配符
                if any("{sample}" in out or "{input_basename}" in out for out in output_files):
                    log_file = log_file.replace(".log", "_{sample}.log")
            rule_parts.append(f'    log: "{log_file}"')
        else:
            # 检查输出文件是否包含通配符
            if any("{sample}" in out or "{input_basename}" in out for out in output_files):
                rule_parts.append(f'    log: "logs/{self.node_id}_{{sample}}.log"')
            else:
                rule_parts.append(f'    log: "logs/{self.node_id}.log"')
        
        # Shell 命令：调用 Python 脚本
        # 脚本应该接受标准化的参数：--input, --output, --params (JSON)
        shell_cmd = self._generate_shell_command(
            input_files, 
            output_files,
            input_files_map=input_files_map
        )
        rule_parts.append("    shell:")
        # 如果命令较长，使用多行格式
        if len(shell_cmd) > 80 or "\\" in shell_cmd:
            # 已经是多行格式
            rule_parts.append(f'        """')
            rule_parts.append(f'        {shell_cmd}')
            rule_parts.append(f'        """')
        else:
            rule_parts.append(f'        "{shell_cmd}"')
        
        return "\n".join(rule_parts) + "\n"
    
    def _generate_shell_command(
        self,
        input_files: List[str],
        output_files: List[str],
        input_files_map: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        生成 shell 命令
        
        支持两种模式：
        1. 命令行工具模式：直接调用可执行文件
        2. 脚本模式：通过 Python 调用脚本
        
        Args:
            input_files: 输入文件列表
            output_files: 输出文件列表
            
        Returns:
            Shell 命令字符串
        """
        tool_type = self.tool_type or self.params.get("tool_type", "script")  # "command" 或 "script"
        
        if tool_type == "command":
            # 命令行工具模式：直接调用可执行文件
            return self._generate_command_tool_shell(input_files, output_files, input_files_map)
        else:
            # 脚本模式：通过 Python 调用脚本
            return self._generate_script_shell(input_files, output_files)
    
    def _generate_command_tool_shell(
        self,
        input_files: List[str],
        output_files: List[str],
        input_files_map: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        生成命令行工具的 shell 命令
        
        Args:
            input_files: 输入文件列表
            output_files: 输出文件列表
            
        Returns:
            Shell 命令字符串
        """
        # 获取工具可执行文件路径
        tool_path = self.params.get("tool_path", self.script_path)
        if not tool_path:
            raise ValueError(f"Node {self.node_id}: tool_path is required for command tool")
        
        # 构建命令
        cmd_parts = [self._normalize_path(tool_path)]
        
        # 获取位置参数列表（如 toppic 的 fasta_file）
        positional_params = self.params.get("positional_params", [])
        if not positional_params and self.node_type in self.tool_registry:
            positional_params = self.tool_registry[self.node_type].get("positional_params", [])
        
        # 获取参数映射（从注册表或 params）
        param_mapping = self.params.get("param_mapping", {})
        if not param_mapping and self.node_type in self.tool_registry:
            param_mapping = self.tool_registry[self.node_type].get("param_mapping", {})
        
        # 第一步：添加所有选项参数（-a, -c, --flag 等）
        for key, value in self.params.items():
            # 跳过元数据参数
            if key in ["script_path", "tool_path", "tool_type", "input_params", 
                       "output_patterns", "input_files", "output_dir", "param_mapping",
                       "input_flag", "output_flag", "conda_env", "positional_params",
                       "output_flag_supported"]:
                continue
            
            # 跳过位置参数（在后面单独处理）
            if key in positional_params:
                continue
            
            # 跳过 None 或空值
            if value is None or value == "":
                continue
            
            # 获取参数标志（从 param_mapping 或使用默认格式）
            if key in param_mapping:
                mapping = param_mapping[key]
                flag = mapping.get("flag", f"--{key.replace('_', '-')}")
                param_type = mapping.get("type", "value")
                
                # 根据类型处理参数
                if param_type == "boolean":
                    if value:
                        cmd_parts.append(flag)
                else:
                    # 值参数（包括 "value" 和 "choice" 类型）
                    # 在 Snakemake 中使用 {params.key} 引用参数
                    cmd_parts.append(flag)
                    cmd_parts.append(f"{{params.{key}}}")
            else:
                # 没有映射，使用默认格式（下划线转连字符）
                flag = f"--{key.replace('_', '-')}"
                if isinstance(value, bool):
                    if value:
                        cmd_parts.append(flag)
                else:
                    cmd_parts.append(flag)
                    cmd_parts.append(f"{{params.{key}}}")
        
        # 第二步：添加位置参数（如 toppic 的 fasta_file）
        for pos_param in positional_params:
            # 优先检查是否是输入文件参数
            if input_files_map and pos_param in input_files_map:
                 # 使用 Snakemake 的输入引用
                 cmd_parts.append(f"{{input.{pos_param}}}")
                 continue
                 
            if pos_param in self.params:
                value = self.params[pos_param]
                if value:
                    # 在 Snakemake 中使用 {params.key} 引用参数
                    cmd_parts.append(f"{{params.{pos_param}}}")
        
        # 第三步：添加输入文件（作为位置参数）
        # 如果有命名输入（多个输入参数），使用 {input.param_name}
        if input_files_map and len(input_files_map) > 1:
            # 多个命名输入，按顺序添加
            # 对于 toppic，第一个输入是 ms2_file，第二个是 feature_file（如果存在）
            for param_name in ["ms2_file", "feature_file", "input_files"]:
                if param_name in input_files_map and input_files_map[param_name]:
                    cmd_parts.append(f"{{input.{param_name}}}")
                    break
            # 如果上面的循环没有添加，添加第一个可用的输入
            if not any("{{input." in p for p in cmd_parts):
                for param_name, files in input_files_map.items():
                    if files:
                        cmd_parts.append(f"{{input.{param_name}}}")
                        break
        elif len(input_files) == 1:
            inp = input_files[0]
            # 在 Snakemake 中使用 {input} 引用输入文件
            if "{sample}" in inp or inp.startswith("results/") or inp.startswith("topfd_") or inp.startswith("toppic_"):
                # 如果是通配符路径，使用 {input}
                cmd_parts.append("{input}")
            else:
                # 如果是绝对路径，直接使用（但如果是模板，使用 {input}）
                if "{sample}" in inp:
                    cmd_parts.append("{input}")
                else:
                    cmd_parts.append(f"'{inp}'")
        else:
            # 多个输入文件，使用 {input} 列表（Snakemake 会自动展开）
            cmd_parts.append("{input}")
        
        # 检查是否支持输出目录选项
        output_flag_supported = self.params.get("output_flag_supported", True)
        if not output_flag_supported and self.node_type in self.tool_registry:
            output_flag_supported = self.tool_registry[self.node_type].get("output_flag_supported", True)

        # 如果支持输出标志且提供了 output_flag，则传递输出目录
        if output_flag_supported:
            out_flag = self.params.get("output_flag")
            if not out_flag and self.node_type in self.tool_registry:
                out_flag = self.tool_registry[self.node_type].get("output_flag")
            if out_flag:
                # 目标目录：单输出使用其父目录，多输出使用当前工作目录
                if len(output_files) == 1:
                    cmd_parts.append(out_flag)
                    cmd_parts.append("$(dirname {output})")
                else:
                    cmd_parts.append(out_flag)
                    cmd_parts.append(".")

        # 对于不支持 -o 选项的工具，输出文件在输入文件同目录自动生成
        # 需要在命令执行后移动输出文件到目标位置
        if not output_flag_supported and output_files:
            # 构建移动文件的命令
            # 需要推导输出文件的实际路径（基于输入文件路径）
            # 对于 topfd: input.mzML -> input_ms2.msalign
            # 对于 toppic: input.msalign -> input.prsm
            move_cmds = []
            for i, out_file in enumerate(output_files):
                if i < len(input_files):
                    inp = input_files[i]
                    # 从输出模式推导实际输出文件名
                    output_patterns = self.params.get("output_patterns", [])
                    if not output_patterns and self.node_type in self.tool_registry:
                        output_patterns = self.tool_registry[self.node_type].get("output_patterns", [])
                    
                    if output_patterns:
                        pattern = output_patterns[0].get("pattern", "")
                        # 提取文件名部分（去掉目录）
                        if "/" in pattern:
                            actual_output_name = pattern.split("/")[-1]
                        else:
                            actual_output_name = pattern
                        # 替换 {input_basename} 为实际输入文件名（去掉扩展名）
                        if "{input_basename}" in actual_output_name:
                            # 在 Snakemake 中，我们需要使用 Python 表达式来推导输出文件名
                            # 但更简单的方法是：使用 shell 命令来推导
                            # 对于 topfd: 输入是 {input}，输出是 $(basename {input} .mzML)_ms2.msalign
                            if "msalign" in actual_output_name:
                                # topfd: input.mzML -> input_ms2.msalign
                                move_cmd = f"mv $(dirname {{input}})/$(basename {{input}} .mzML)_ms2.msalign {{output}}"
                            elif "prsm" in actual_output_name:
                                # toppic: input.msalign -> input.prsm
                                move_cmd = f"mv $(dirname {{input}})/$(basename {{input}} .msalign).prsm {{output}}"
                            else:
                                # 通用情况：使用输出模式
                                move_cmd = f"mv $(dirname {{input}})/{actual_output_name.replace('{input_basename}', '$(basename {{input}} .$(echo {{input}} | cut -d. -f2))')} {{output}}"
                            move_cmds.append(move_cmd)
            
            if move_cmds:
                # 组合命令：先运行工具，然后移动输出文件
                tool_cmd = " ".join(cmd_parts)
                move_cmd = " && ".join(move_cmds)
                return f"{tool_cmd} && {move_cmd}"
        
        return " ".join(cmd_parts)
    
    def _generate_script_shell(
        self,
        input_files: List[str],
        output_files: List[str]
    ) -> str:
        """
        生成脚本工具的 shell 命令
        
        脚本接口约定：
        - --input: 输入文件（可以多个）
        - --output: 输出文件（可以多个）
        - --params: JSON 格式的参数（可选）
        
        Args:
            input_files: 输入文件列表
            output_files: 输出文件列表
            
        Returns:
            Shell 命令字符串
        """
        # 确定 Python 解释器
        python_cmd = "python3" if self.platform == "linux" else "python"
        
        # 构建命令
        cmd_parts = [python_cmd, self.script_path]
        
        if self.node_type == "fasta_loader":
            fasta_val = self.params.get("fasta_file") or self.params.get("fasta")
            if fasta_val:
                cmd_parts.append(f"--fasta '{str(fasta_val)}'")
            if output_files:
                cmd_parts.append(f"--output '$(dirname {{output}})'")
            else:
                cmd_parts.append("--output '.'")
        else:
            for inp in input_files:
                cmd_parts.append(f"--input '{inp}'")
            for out in output_files:
                cmd_parts.append(f"--output '{out}'")
        
        # 添加参数（作为 JSON 字符串）
        import json
        params_dict = {}
        for key, value in self.params.items():
            if key not in ["script_path", "tool_path", "tool_type", "input_params", 
                          "output_patterns", "input_files", "output_dir", "param_mapping"]:
                params_dict[key] = value
        
        if params_dict:
            params_json = json.dumps(params_dict).replace('"', '\\"')
            params_json = params_json.replace("{", "{{").replace("}", "}}")
            cmd_parts.append(f"--params '{params_json}'")
        
        return " ".join(cmd_parts)
    
    def _normalize_path(self, path: str) -> str:
        """
        标准化路径（根据平台）
        
        Args:
            path: 原始路径
            
        Returns:
            标准化后的路径
        """
        if self.platform == "windows":
            return path.replace('/', '\\')
        else:
            return path.replace('\\', '/')
