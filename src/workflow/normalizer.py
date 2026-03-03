from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class WorkflowNormalizer:
    def normalize(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        wf = {}
        metadata = workflow.get("metadata", {}) or {}
        wf["metadata"] = {
            "id": metadata.get("id"),
            "name": metadata.get("name"),
            "version": metadata.get("version"),
            "created": metadata.get("created"),
            "modified": metadata.get("modified"),
            "author": metadata.get("author"),
            "tags": metadata.get("tags", []),
            "uuid": metadata.get("uuid"),
            "license": metadata.get("license"),
            "creator": metadata.get("creator"),
            "sample_context": metadata.get("sample_context"),
            "samples": metadata.get("samples"),
        }
        wf["format_version"] = workflow.get("format_version") or workflow.get("format-version") or "2.0"
        wf["schema_version"] = "2.0"
        project_settings = workflow.get("projectSettings", {}) or workflow.get("workflow", {}) or {}
        wf["projectSettings"] = project_settings
        
        # Preserve VueFlow nodes and connections for UI rendering
        nodes: List[Dict[str, Any]] = []
        for n in workflow.get("nodes", []):
            data_cfg = (n.get("data", {}) or {})
            node_cfg = n.get("nodeConfig", {}) or {}
            tool_id = data_cfg.get("type") or node_cfg.get("toolId") or n.get("type")
            params = data_cfg.get("params") or node_cfg.get("paramValues") or {}
            nodes.append({"id": n.get("id"), "data": {"type": tool_id, "params": params}})
        wf["nodes"] = nodes
        
        edges_in = workflow.get("edges") or workflow.get("connections") or []
        edges: List[Dict[str, Any]] = []
        for c in edges_in:
            src = c.get("source")
            tgt = c.get("target")
            if isinstance(src, dict):
                src_id = src.get("nodeId") or src.get("id")
                src_handle = src.get("portId") or c.get("sourceHandle")
            else:
                src_id = src
                src_handle = c.get("sourceHandle")
            if isinstance(tgt, dict):
                tgt_id = tgt.get("nodeId") or tgt.get("id")
                tgt_handle = tgt.get("portId") or c.get("targetHandle")
            else:
                tgt_id = tgt
                tgt_handle = c.get("targetHandle")
            edges.append({
                "id": c.get("id"),
                "source": src_id,
                "target": tgt_id,
                "sourceHandle": self._normalize_handle(src_handle),
                "targetHandle": self._normalize_handle(tgt_handle),
            })
        wf["edges"] = edges
        
        # Generate Galaxy format steps, inputs, and outputs from nodes and connections
        wf["steps"] = self._generate_steps(workflow.get("nodes", []), edges)
        wf["inputs"], wf["outputs"] = self._generate_inputs_outputs(workflow.get("nodes", []), edges)
        
        return wf
    
    def _generate_steps(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Generate Galaxy format steps from VueFlow nodes"""
        steps: Dict[str, Dict[str, Any]] = {}
        
        # Build node connections map for input resolution
        node_inputs: Dict[str, Dict[str, str]] = {}  # node_id -> {input_port: source_step/output_port}
        
        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")
            source_handle = edge.get("sourceHandle")
            target_handle = edge.get("targetHandle")
            
            if target_id not in node_inputs:
                node_inputs[target_id] = {}
            # Format: "step_name/output_port"
            if source_handle and target_handle:
                node_inputs[target_id][target_handle] = f"{source_id}/{source_handle}"
        
        for node in nodes:
            node_id = node.get("id")
            data_cfg = node.get("data", {}) or {}
            node_cfg = node.get("nodeConfig", {}) or {}
            tool_id = data_cfg.get("type") or node_cfg.get("toolId") or node.get("type")
            params = data_cfg.get("params") or node_cfg.get("paramValues") or {}
            position = node.get("position", {})
            
            # Determine step type
            step_type = "tool"
            if tool_id in ["data_loader", "fasta_loader"]:
                step_type = "data_input"
            
            step: Dict[str, Any] = {
                "id": node_id,
                "type": step_type,
                "tool_state": params if step_type == "tool" else {},
            }
            
            if step_type == "tool":
                step["tool_id"] = tool_id
            
            # Add inputs (connections from other steps)
            if node_id in node_inputs:
                step["inputs"] = node_inputs[node_id]
            
            # Add outputs (default output ports based on node type)
            step["outputs"] = self._get_default_outputs(tool_id)
            
            if position:
                step["position"] = {"x": position.get("x", 0.0), "y": position.get("y", 0.0)}
            
            steps[node_id] = step
        
        return steps
    
    def _get_default_outputs(self, tool_id: str) -> Dict[str, str]:
        """Get default output ports for a tool type"""
        # Default output mappings - can be extended based on tool registry
        defaults = {
            "data_loader": {"output": "data_loader/output"},
            "fasta_loader": {"output": "fasta_loader/output"},
        }
        return defaults.get(tool_id, {"output": f"{tool_id}/output"})
    
    def _generate_inputs_outputs(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """Generate Galaxy format workflow inputs and outputs"""
        inputs: Dict[str, Dict[str, Any]] = {}
        outputs: Dict[str, Dict[str, Any]] = {}
        
        # Find input nodes (data_loader, fasta_loader, etc.) as workflow inputs
        input_counter = 0
        for node in nodes:
            data_cfg = node.get("data", {}) or {}
            tool_id = data_cfg.get("type") or node.get("type")
            node_id = node.get("id")
            
            if tool_id in ["data_loader", "fasta_loader"]:
                input_id = f"input{input_counter + 1}"
                inputs[input_id] = {
                    "id": input_id,
                    "type": "data",
                    "label": f"{tool_id}_{node_id}",
                }
                input_counter += 1
        
        # Find terminal nodes (nodes with no outgoing edges) as workflow outputs
        source_nodes = {edge.get("source") for edge in edges}
        output_counter = 0
        
        for node in nodes:
            node_id = node.get("id")
            # If node has no outgoing edges, it's a potential output
            if node_id not in source_nodes:
                output_id = f"output{output_counter + 1}"
                # Find the last output port (default to "output")
                outputs[output_id] = {
                    "id": output_id,
                    "outputSource": f"{node_id}/output",
                    "label": f"output_{node_id}",
                }
                output_counter += 1
        
        return inputs, outputs

    def _normalize_handle(self, h: Optional[str]) -> Optional[str]:
        """
        归一化端口句柄，保留完整的 input-XXX / output-XXX 前缀语义信息。
        这些前缀对于理解数据流向很重要，不应该被移除。
        """
        return h  # 直接返回原始值，保留完整语义
