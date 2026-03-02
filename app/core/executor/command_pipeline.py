"""
Command Pipeline - Build CLI commands from Tool Definition Schema

This module implements a pipeline approach to command building:
1. Filter empty parameters
2. Resolve executable command
3. Add output flag
4. Add parameter flags
5. Add positional arguments

Replaces the old CommandBuilder with a unified, schema-driven approach.
"""
import logging
import shlex
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


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

    def __init__(self, tool_def: Dict[str, Any]):
        """
        Initialize command pipeline with tool definition.

        Args:
            tool_def: Tool definition from config/tools/*.json
        """
        self.tool_def = tool_def
        self.execution_mode = tool_def.get("executionMode", "native")
        self.command_config = tool_def.get("command", {})
        self.ports = tool_def.get("ports", {})
        self.parameters = tool_def.get("parameters", {})
        self.output_config = tool_def.get("output", {})

    def build(
        self,
        param_values: Dict[str, Any],
        input_files: Dict[str, str],
        output_dir: Optional[str] = None
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
        # Step 1: Filter empty parameters
        filtered_params = self._filter_empty_params(param_values)

        # Step 2: Resolve executable
        executable = self._resolve_executable()
        cmd_parts = [executable]

        # Step 3: Add output flag
        if output_dir and self.output_config.get("flagSupported"):
            output_flag = self.output_config.get("flag", "-o")
            output_value = self.output_config.get("flagValue", output_dir)
            cmd_parts.extend([output_flag, output_value])

        # Step 4: Add parameter flags
        cmd_parts.extend(self._build_parameter_flags(filtered_params))

        # Step 5: Add positional arguments
        cmd_parts.extend(self._build_positional_args(input_files))

        return cmd_parts

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
            interpreter = self.command_config.get("interpreter", "")
            use_uv = self.command_config.get("useUv", False)

            if interpreter == "python":
                if use_uv:
                    return "uv"
                else:
                    return "python" if platform.system() != "Windows" else "python.exe"
            elif interpreter == "Rscript":
                return "Rscript"
            elif interpreter in ("bash", "sh"):
                return interpreter
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
                    # Quote the value if it contains spaces
                    if isinstance(value, str) and (" " in value or "\t" in value):
                        flags.extend([flag, self._quote_value(value)])
                    else:
                        flags.extend([flag, str(value)])

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
            file_path = input_files.get(port_id, "")
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
    output_dir: Optional[str] = None
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
    return pipeline.build(param_values, input_files, output_dir)


def build_command_string(
    tool_def: Dict[str, Any],
    param_values: Dict[str, Any],
    input_files: Dict[str, str],
    output_dir: Optional[str] = None
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
    parts = build_command(tool_def, param_values, input_files, output_dir)
    return " ".join(parts)
