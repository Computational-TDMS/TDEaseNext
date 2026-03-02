from pathlib import Path

def get_workflows_root() -> str:
    return str(Path(__file__).parent.parent.parent / "data" / "workflows")
