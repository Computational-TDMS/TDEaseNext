"""
Command Pipeline - Build CLI commands from Tool Definition Schema

This module implements a pipeline approach to command building:
1. Filter empty parameters
2. Resolve executable command
3. Add output flag
4. Add parameter flags
5. Add params JSON (use_params_json 时)
6. Add positional arguments

Replaces the old CommandBuilder with a unified, schema-driven approach.
"""
import json
import logging
import shlex
import platform
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Project root: app/core/executor/command_pipeline.py -> ../../../ = project
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass
class CommandAssemblyTrace:
    tool_id: str
    execution_mode: str
    executable: str
    filtered_params: Dict[str, Any]
    input_files: Dict[str, str]
    output_target: str
    output_flag: Dict[str, str]
    parameter_flags: List[str]
    input_flags: List[str]
    params_json: str
    positional_args: List[str]
    cmd_parts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CommandPipeline:
    """
    Build CLI commands from Tool Definition Schema.

    Uses a 5-step pipeline:
    1. Filter: Remove null/empty/"none" values
    2. Executable: Resolve command based on executionMode
    3. Output: Add output flag if supported
    4. Parameters: Add parameter flags
    5. Positional: Add positional arguments in order
    """

    def __init__(self, tool_def: Dict[str, Any], preview_mode: bool = False):
        """
        Initialize command pipeline with tool definition.

        Args:
            tool_def: Tool definition from config/tools/*.json
            preview_mode: If True, use placeholders instead of actual file paths
        """
        self.tool_def = tool_def
        self.execution_mode = tool_def.get("executionMode", "native")
        self.command_config = tool_def.get("command", {})
        self.ports = tool_def.get("ports", {})
        self.parameters = tool_def.get("parameters", {})
        self.output_config = tool_def.get("output", {})
        self.preview_mode = preview_mode

    def build(
        self,
        param_values: Dict[str, Any],
        input_files: Dict[str, str],
        output_target: Optional[str] = None
    ) -> List[str]:
        """
        Build complete command as list of arguments.

        Args:
            param_values: User-provided parameter values
            input_files: Input file paths (port_id -> path)
            output_dir: Output directory path

        Returns:
            List of command arguments (e.g., ["toppic", "-a", "21.0", "db.fasta", "input.msalign"])
        """
        cmd_parts, _trace = self.build_with_trace(param_values, input_files, output_target)
        return cmd_parts

    def build_with_trace(
        self,
        param_values: Dict[str, Any],
        input_files: Dict[str, str],
        output_target: Optional[str] = None
    ) -> Tuple[List[str], CommandAssemblyTrace]:
        # Step 1: Filter empty parameters
        filtered_params = self._filter_empty_params(param_values)

        # Step 2: Resolve executable
        executable = self._resolve_executable()

        logger.info(f"[CommandPipeline] Building command for tool: {self.tool_def.get('id', 'unknown')}")
        logger.info(f"[CommandPipeline] input_files: {input_files}")
        logger.info(f"[CommandPipeline] filtered_params: {filtered_params}")

        # cmd_parts 为原始参数列表，由 LocalExecutor 用 list2cmdline/shlex.join 统一加引号，此处不包一层引号
        cmd_parts: List[str] = []
        if self.execution_mode == "script":
            parts = executable.split(" ")
            for part in parts:
                if part:
                    cmd_parts.append(part)
        else:
            if executable:
                cmd_parts = [executable]

        output_flag_info = {"flag": "", "value": ""}
        # Step 3: Add output flag (path or directory depending on tool config)
        if self.output_config.get("flagSupported"):
            output_flag = self.output_config.get("flag", "-o")

            # In preview mode, use placeholder if no output target provided
            if self.preview_mode:
                output_value = output_target or "<output_dir>"
            elif output_target:
                output_dir = str(Path(output_target).parent)
                template = self.output_config.get("flagValue")
                if template:
                    output_value = template.format(output_path=output_target, output_dir=output_dir)
                else:
                    output_value = output_dir
            else:
                output_value = None

            if output_value:
                output_flag_info = {"flag": output_flag, "value": output_value}
                cmd_parts.extend([output_flag, output_value])

        # Step 4: Add parameter flags
        parameter_flags = self._build_parameter_flags(filtered_params)
        cmd_parts.extend(parameter_flags)

        # Step 4b: Add input flags (for inputs with flag attribute)
        input_flags = self._build_input_flags(input_files)
        logger.info(f"[CommandPipeline] input_flags: {input_flags}")
        cmd_parts.extend(input_flags)

        # Step 4c: Add --params JSON for scripts that need extra params (e.g. sample_name)
        params_json = ""
        if self.tool_def.get("useParamsJson") or self.tool_def.get("use_params_json"):
            # 排除前端/内部字段，只传脚本需要的参数
            internal_keys = {"tool_type", "type"}
            params_for_json = {k: v for k, v in filtered_params.items() if k not in internal_keys}
            params_json = json.dumps(params_for_json)
            cmd_parts.extend(["--params", params_json])

        # Step 5: Add positional arguments
        positional_args = self._build_positional_args(input_files)
        logger.info(f"[CommandPipeline] positional_args: {positional_args}")
        cmd_parts.extend(positional_args)

        logger.info(f"[CommandPipeline] Final cmd_parts: {cmd_parts}")
        trace = CommandAssemblyTrace(
            tool_id=self.tool_def.get("id", "unknown"),
            execution_mode=self.execution_mode,
            executable=executable,
            filtered_params=filtered_params,
            input_files=dict(input_files),
            output_target=output_target or "",
            output_flag=output_flag_info,
            parameter_flags=parameter_flags,
            input_flags=input_flags,
            params_json=params_json,
            positional_args=positional_args,
            cmd_parts=list(cmd_parts),
        )
        return cmd_parts, trace

    def _filter_empty_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1: Filter out null, empty, and "none" values.

        This is the FIRST step in the pipeline, ensuring clean data
        before any command building logic.
        """
        filtered = {}
        for key, value in params.items():
            # Skip None values
            if value is None:
                continue

            # Skip empty strings
            if isinstance(value, str) and value.strip() == "":
                continue

            # Skip "none" strings (case-insensitive)
            if isinstance(value, str) and value.strip().lower() == "none":
                continue

            # Skip empty lists/dicts
            if isinstance(value, (list, dict)) and len(value) == 0:
                continue

            filtered[key] = value

        return filtered

    def _resolve_executable(self) -> str:
        """
        Step 2: Resolve executable command based on executionMode.

        Returns the base command or script path.
        """
        if self.execution_mode == "native":
            # Native command: use executable directly
            return self.command_config.get("executable", "")

        elif self.execution_mode == "script":
            # Script mode: wrap with interpreter
            executable = self.command_config.get("executable", "")
            # Resolve relative paths against project root (Shell runs in workspace dir)
            if executable and not os.path.isabs(executable):
                resolved = (_PROJECT_ROOT / executable).resolve()
                if resolved.exists():
                    executable = str(resolved)
            interpreter = self.command_config.get("interpreter", "")
            use_uv = self.command_config.get("useUv", False)

            if interpreter == "python":
                if use_uv:
                    # uv run <script>
                    return f"uv run {executable}"
                else:
                    cmd = "python" if platform.system() != "Windows" else "python.exe"
                    return f"{cmd} {executable}"
            elif interpreter == "Rscript":
                return f"Rscript {executable}"
            elif interpreter in ("bash", "sh"):
                return f"{interpreter} {executable}"
            else:
                return executable

        elif self.execution_mode == "docker":
            # Docker mode: docker run <image> <command>
            # Just return the docker run prefix
            return "docker"

        elif self.execution_mode == "interactive":
            # Interactive mode: no command execution
            return ""

        return ""

    def _build_parameter_flags(self, params: Dict[str, Any]) -> List[str]:
        """
        Step 4: Build parameter flags from filtered values.

        Handles three types:
        - value: -f value
        - boolean: -f (if true)
        - choice: flag or choice-specific flag
        """
        flags = []

        for param_id, value in params.items():
            param_def = self.parameters.get(param_id, {})
            if not param_def:
                continue

            param_type = param_def.get("type", "value")
            flag = param_def.get("flag", "")

            if param_type == "boolean":
                if value is True:
                    flags.append(flag)

            elif param_type == "choice":
                choices = param_def.get("choices", {})
                if value in choices:
                    flags.append(choices[value])

            elif param_type == "value":
                if value is not None and value != "":
                    # Handle lists (e.g., multiple input files)
                    if isinstance(value, list):
                        # Add flag once, then all values
                        flags.append(flag)
                        flags.extend([str(v) for v in value])
                    # Handle strings
                    elif isinstance(value, str):
                        flags.extend([flag, value])
                    # Handle other types
                    else:
                        flags.extend([flag, str(value)])

        return flags

    def _build_input_flags(self, input_files: Dict[str, str]) -> List[str]:
        """
        Step 4b: Build flag arguments for input ports that have a 'flag' attribute.

        Input ports can specify a flag (e.g., "-s") to be used instead of positional.
        """
        flags = []
        inputs = self.ports.get("inputs", [])

        for inp in inputs:
            port_id = inp.get("id", "")
            flag = inp.get("flag", "")

            # Skip if no flag or if it's a positional input
            if not flag or inp.get("positional", False):
                continue

            # In preview mode, use placeholder if no file path provided
            if self.preview_mode:
                file_path = input_files.get(port_id, f"<{port_id}>")
            else:
                file_path = input_files.get(port_id, "")

            # Skip if no file path (unless in preview mode)
            if not file_path:
                continue

            # Add flag and file path
            flags.extend([flag, file_path])

        return flags

    def _build_positional_args(self, input_files: Dict[str, str]) -> List[str]:
        """
        Step 5: Build positional arguments from input ports.

        Ports with positional=true are ordered by positionalOrder.
        """
        args = []

        # Get input ports with positional=true
        inputs = self.ports.get("inputs", [])
        positional_inputs = [
            inp for inp in inputs
            if inp.get("positional", False)
        ]

        # Sort by positionalOrder
        positional_inputs.sort(key=lambda x: x.get("positionalOrder", 0))

        # Build arguments
        for inp in positional_inputs:
            port_id = inp.get("id", "")

            # In preview mode, use placeholder if no file path provided
            if self.preview_mode:
                file_path = input_files.get(port_id, f"<{port_id}>")
            else:
                file_path = input_files.get(port_id, "")

            # Skip if no file path (unless in preview mode)
            if file_path:
                args.append(file_path)

        return args

    def _quote_value(self, value: str) -> str:
        """
        Shell-quote a value for safe command-line passing.
        """
        if platform.system() == "Windows":
            # Windows: use double quotes
            if '"' in value:
                # Escape existing quotes
                value = value.replace('"', '\\"')
            return f'"{value}"'
        else:
            # Unix: use shlex.quote
            return shlex.quote(value)


def build_command(
    tool_def: Dict[str, Any],
    param_values: Dict[str, Any],
    input_files: Dict[str, str],
    output_target: Optional[str] = None
) -> List[str]:
    """
    Convenience function to build a command from tool definition.

    Args:
        tool_def: Tool definition dictionary
        param_values: User-provided parameter values
        input_files: Input file paths (port_id -> path)
        output_dir: Output directory path

    Returns:
        List of command arguments
    """
    pipeline = CommandPipeline(tool_def)
    return pipeline.build(param_values, input_files, output_target)


def build_command_with_trace(
    tool_def: Dict[str, Any],
    param_values: Dict[str, Any],
    input_files: Dict[str, str],
    output_target: Optional[str] = None
) -> Tuple[List[str], CommandAssemblyTrace]:
    """
    Build command and return structured assembly trace.
    """
    pipeline = CommandPipeline(tool_def)
    return pipeline.build_with_trace(param_values, input_files, output_target)


def build_command_string(
    tool_def: Dict[str, Any],
    param_values: Dict[str, Any],
    input_files: Dict[str, str],
    output_target: Optional[str] = None
) -> str:
    """
    Build command as a single string (for display/logging).

    Args:
        tool_def: Tool definition dictionary
        param_values: User-provided parameter values
        input_files: Input file paths (port_id -> path)
        output_dir: Output directory path

    Returns:
        Command as a single string
    """
    parts = build_command(tool_def, param_values, input_files, output_target)
    return " ".join(parts)
