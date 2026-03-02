import json
from typing import Any, Dict, Tuple

def detect_workflow_format(document: str) -> str:
    """
    Detect workflow format from document string.
    
    Currently supports:
    - VueFlow JSON format (our primary format)
    - Galaxy .ga format (legacy support)
    - Galaxy Format2 YAML/JSON (legacy support)
    """
    doc = document.strip()
    if doc.startswith("{"):
        try:
            data = json.loads(doc)
            # Check for VueFlow format (our primary format)
            if "nodes" in data and "edges" in data:
                return "vueflow"
            # Check for Galaxy .ga format
            if "a_galaxy_workflow" in data and "format-version" in data:
                return "ga"
            # Format2 JSON variant
            if data.get("class") == "GalaxyWorkflow":
                return "format2_json"
        except Exception:
            return "unknown"
    # Assume YAML when not JSON
    if "class: GalaxyWorkflow" in doc or "class: GalaxyWorkflow" in doc.replace(" ", ""):
        return "format2_yaml"
    return "unknown"


def validate_workflow_document(document: str) -> Tuple[bool, str, Any]:
    """
    Validate workflow document.
    
    For VueFlow format, performs basic validation.
    For Galaxy formats, performs format detection only (full validation requires Galaxy models).
    """
    fmt = detect_workflow_format(document)
    try:
        if fmt == "vueflow":
            # Basic validation for VueFlow format
            data = json.loads(document)
            if not isinstance(data, dict):
                return False, fmt, "Workflow must be a JSON object"
            if "nodes" not in data:
                return False, fmt, "Workflow must have 'nodes' field"
            if "edges" not in data:
                return False, fmt, "Workflow must have 'edges' field"
            return True, fmt, data
        elif fmt in ("ga", "format2_json", "format2_yaml"):
            # Galaxy format detection only - full validation would require Galaxy models
            # For now, we accept the format if it's detected correctly
            if fmt == "format2_yaml":
                import yaml
                data = yaml.safe_load(document)
            else:
                data = json.loads(document)
            return True, fmt, data
        else:
            return False, fmt, "Unknown workflow document format"
    except json.JSONDecodeError as e:
        return False, fmt, f"Invalid JSON: {e}"
    except Exception as e:
        return False, fmt, f"Parse error: {e}"

