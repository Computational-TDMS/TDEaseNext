from typing import Dict, Any


class PathRouter:
    def __init__(self, registry: Dict[str, Dict[str, Any]]):
        self.registry = registry

    def build_routing(self, workflow: Dict[str, Any], workdir: str = "results") -> Dict[str, Any]:
        routing: Dict[str, Any] = {"workdir": workdir, "nodes": {}}
        nodes = workflow.get("nodes", [])
        for n in nodes:
            data_cfg = (n.get("data", {}) or {})
            node_type = data_cfg.get("type") or (n.get("nodeConfig", {}) or {}).get("id")
            node_id = n.get("id")
            tool_info = self.registry.get(node_type or "", {})
            output_patterns = tool_info.get("output_patterns", [])
            node_map: Dict[str, str] = {}
            for p in output_patterns:
                pat = p.get("pattern") or "{sample}.out"
                handle = p.get("handle") or "output"
                node_map[handle] = pat
            routing["nodes"][node_id] = {"type": node_type, "outputs": node_map}
        return routing
