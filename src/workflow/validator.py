from typing import Dict, Any, List, Set
from pathlib import Path
import os
import re

class WorkflowValidator:
    def validate(self, workflow_v2: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[Dict[str, Any]] = []
        
        # Validate Galaxy format structure if present
        steps = workflow_v2.get("steps")
        if steps:
            errors.extend(self._validate_steps(steps))
        
        inputs = workflow_v2.get("inputs")
        outputs = workflow_v2.get("outputs")
        if inputs and outputs:
            errors.extend(self._validate_inputs_outputs(inputs, outputs, steps or {}))
        
        # Validate samples: 有 data_loader 时要求 input_sources；无 data_loader 时使用默认 sample（如纯 ABC 流程）
        samples = self._derive_samples(workflow_v2)
        sample_paths = self._derive_sample_paths(workflow_v2)
        has_data_loader = any(
            (n.get("data", {}) or {}).get("type") == "data_loader"
            for n in workflow_v2.get("nodes", [])
        )
        if has_data_loader:
            if not samples:
                errors.append({"code": "NO_SAMPLES", "message": "缺少样本列表：请在 data_loader 节点的 input_sources 中提供原始文件"})
            if not sample_paths:
                errors.append({"code": "NO_SAMPLE_PATHS", "message": "缺少样本路径映射：请设置可访问的绝对路径"})
            for s in samples:
                if s not in sample_paths:
                    errors.append({"code": "SAMPLE_PATH_MISSING", "message": f"样本 '{s}' 缺少原始文件映射", "field": "sample_paths"})
            for k, v in sample_paths.items():
                if not os.path.isabs(v) or not os.path.exists(v):
                    errors.append({"code": "PATH_INVALID", "message": f"样本 '{k}' 的路径不可访问: {v}", "field": "sample_paths"})
        else:
            samples = ["default"]
            sample_paths = {}
        return {"samples": samples, "sample_paths": sample_paths, "errors": errors}
    
    def _validate_steps(self, steps: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate Galaxy format steps structure"""
        errors: List[Dict[str, Any]] = []
        for step_id, step in steps.items():
            if not isinstance(step, dict):
                errors.append({"code": "INVALID_STEP", "message": f"Step '{step_id}' must be a dictionary"})
                continue
            
            if "id" not in step:
                errors.append({"code": "STEP_MISSING_ID", "message": f"Step '{step_id}' missing 'id' field"})
            
            if "type" not in step:
                errors.append({"code": "STEP_MISSING_TYPE", "message": f"Step '{step_id}' missing 'type' field"})
            
            step_type = step.get("type")
            if step_type == "tool" and "tool_id" not in step:
                errors.append({"code": "TOOL_STEP_MISSING_ID", "message": f"Tool step '{step_id}' missing 'tool_id' field"})
        return errors
    
    def _validate_inputs_outputs(self, inputs: Dict[str, Dict[str, Any]], outputs: Dict[str, Dict[str, Any]], steps: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate workflow inputs and outputs reference integrity"""
        errors: List[Dict[str, Any]] = []
        
        # Validate output references
        for output_id, output_def in outputs.items():
            output_source = output_def.get("outputSource")
            if not output_source:
                errors.append({"code": "OUTPUT_MISSING_SOURCE", "message": f"Output '{output_id}' missing 'outputSource'"})
                continue
            
            # Check format: "step_id/output_port"
            if "/" not in output_source:
                errors.append({"code": "INVALID_OUTPUT_SOURCE", "message": f"Output '{output_id}' has invalid 'outputSource' format: '{output_source}' (expected 'step_id/output_port')"})
                continue
            
            step_id, output_port = output_source.split("/", 1)
            if step_id not in steps:
                errors.append({"code": "OUTPUT_REFERENCE_INVALID", "message": f"Output '{output_id}' references non-existent step '{step_id}'"})
        
        return errors

    def _derive_samples(self, workflow_v2: Dict[str, Any]) -> List[str]:
        for node in workflow_v2.get("nodes", []):
            data = node.get("data", {})
            if data.get("type") == "data_loader":
                srcs = data.get("params", {}).get("input_sources", [])
                if isinstance(srcs, str):
                    srcs = [srcs]
                return [Path(str(p)).stem for p in srcs] if isinstance(srcs, list) and srcs else []
        return []

    def _derive_sample_paths(self, workflow_v2: Dict[str, Any]) -> Dict[str, str]:
        sample_paths: Dict[str, str] = {}
        for node in workflow_v2.get("nodes", []):
            data = node.get("data", {})
            if data.get("type") == "data_loader":
                srcs = data.get("params", {}).get("input_sources", [])
                if isinstance(srcs, str):
                    srcs = [srcs]
                if isinstance(srcs, list):
                    for p in srcs:
                        ps = Path(str(p))
                        sample_paths[ps.stem] = str(ps)
        return sample_paths


def extract_required_placeholders(workflow_v2: Dict[str, Any],
                                   tool_registry: Dict[str, Dict]) -> Set[str]:
    """
    Extract all required placeholders from tool output patterns.

    Args:
        workflow_v2: Workflow definition
        tool_registry: Tool registry containing output_patterns

    Returns:
        Set of required placeholder names (e.g., {"sample", "fasta_filename"})
    """
    placeholders = set()

    for node in workflow_v2.get("nodes", []):
        tool_id = node.get("data", {}).get("type")
        if not tool_id:
            continue

        tool_info = tool_registry.get(tool_id, {})
        output_patterns = tool_info.get("output_patterns", [])

        for pattern_info in output_patterns:
            if isinstance(pattern_info, dict):
                pattern = pattern_info.get("pattern", "")
            elif isinstance(pattern_info, str):
                pattern = pattern_info
            else:
                continue

            # Extract {placeholder} from pattern
            extracted = re.findall(r"\{(\w+)\}", pattern)
            placeholders.update(extracted)

    return placeholders


def validate_placeholders(required: Set[str],
                          sample_context: Dict[str, str],
                          pattern_hint: str = "") -> None:
    """
    Validate that sample context contains all required placeholders.

    Args:
        required: Set of required placeholder names
        sample_context: Sample context dictionary
        pattern_hint: Optional pattern string for error message

    Raises:
        ValueError: If any required placeholders are missing
    """
    missing = required - set(sample_context.keys())

    if missing:
        error_msg = f"Missing placeholders: {missing}"
        if pattern_hint:
            error_msg += f" in pattern '{pattern_hint}'"
        error_msg += f". Available: {list(sample_context.keys())}"
        raise ValueError(error_msg)


def validate_sample_placeholders(workflow_v2: Dict[str, Any],
                                 tool_registry: Dict[str, Dict],
                                 samples_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate that all samples provide required placeholders.

    Args:
        workflow_v2: Workflow definition
        tool_registry: Tool registry containing output_patterns
        samples_data: Samples data with "samples" dict

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Extract required placeholders from workflow
    required = extract_required_placeholders(workflow_v2, tool_registry)

    if not required:
        return errors  # No placeholders required

    samples = samples_data.get("samples", {})

    if not samples:
        errors.append({
            "code": "NO_SAMPLES_DEFINED",
            "message": f"Workflow requires placeholders {required}, but no samples defined"
        })
        return errors

    # Validate each sample
    for sample_id, sample_def in samples.items():
        context = sample_def.get("context", {})

        # Check for derived values that would satisfy requirements
        data_paths = sample_def.get("data_paths", {})
        has_raw_path = bool(data_paths.get("raw"))

        # Build effective context (explicit + potential derived)
        effective_context = set(context.keys())

        # "sample" is always available from sample_id
        effective_context.add("sample")

        # If has raw path, input_basename, input_dir, input_ext can be derived
        if has_raw_path:
            effective_context.update(["input_basename", "input_dir", "input_ext"])

        missing = required - effective_context

        if missing:
            errors.append({
                "code": "SAMPLE_MISSING_PLACEHOLDERS",
                "message": f"Sample '{sample_id}' missing placeholders: {missing}",
                "sample_id": sample_id,
                "missing": list(missing)
            })

    return errors
