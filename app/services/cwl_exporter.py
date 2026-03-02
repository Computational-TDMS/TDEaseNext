"""
CWL (Common Workflow Language) exporter service.

Converts workflow JSON from database to CWL format.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml


class CWLExporter:
    """Export workflow JSON to CWL format."""
    
    def __init__(self):
        pass
    
    def export_workflow_to_cwl(
        self,
        workflow_json: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Convert workflow JSON to CWL Workflow format.
        
        Args:
            workflow_json: Workflow JSON from database (VueFlow format)
            tools: Optional list of tool definitions for metadata
            
        Returns:
            CWL workflow dictionary
        """
        # Normalize workflow
        from src.workflow.normalizer import WorkflowNormalizer
        normalizer = WorkflowNormalizer()
        wf_v2 = normalizer.normalize(workflow_json)
        
        metadata = wf_v2.get("metadata", {})
        nodes = wf_v2.get("nodes", [])
        edges = wf_v2.get("edges", [])
        
        # Build tools registry if provided
        tools_registry = {}
        if tools:
            tools_registry = self._build_tools_registry(tools)
        
        # Build node dependency map
        node_dependencies = self._build_dependencies(nodes, edges)
        
        # Build CWL workflow
        cwl_workflow = {
            "cwlVersion": "v1.2",
            "class": "Workflow",
            "label": metadata.get("name", "Workflow"),
            "doc": metadata.get("description") or metadata.get("name", "Workflow"),
        }
        
        # Build inputs
        workflow_inputs = self._build_workflow_inputs(nodes, edges)
        if workflow_inputs:
            cwl_workflow["inputs"] = workflow_inputs
        
        # Build steps (one per node)
        steps = {}
        for node in nodes:
            node_id = node.get("id")
            step_cwl = self._node_to_cwl_step(
                node, edges, node_dependencies, tools_registry
            )
            if step_cwl:
                steps[node_id] = step_cwl
        
        cwl_workflow["steps"] = steps
        
        # Build outputs
        workflow_outputs = self._build_workflow_outputs(nodes, edges)
        if workflow_outputs:
            cwl_workflow["outputs"] = workflow_outputs
        
        return cwl_workflow
    
    def _build_tools_registry(self, tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Build tools registry from tools list."""
        registry = {}
        for tool in tools:
            tool_id = tool.get("id") or tool.get("name")
            if tool_id:
                registry[tool_id] = {
                    "tool_path": tool.get("toolPath") or tool.get("tool_path"),
                    "description": tool.get("description") or tool_id,
                    "inputs": tool.get("inputs", []),
                    "outputs": tool.get("outputs", []),
                }
        return registry
    
    def _build_dependencies(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Build dependency map: node_id -> list of dependent node_ids."""
        dependencies = {node.get("id"): [] for node in nodes}
        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")
            if source_id and target_id and target_id in dependencies:
                dependencies[target_id].append(source_id)
        return dependencies
    
    def _build_workflow_inputs(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build workflow-level inputs (nodes with no incoming edges)."""
        # Find nodes with no incoming edges (these are workflow inputs)
        nodes_with_incoming = {edge.get("target") for edge in edges}
        input_nodes = [
            node for node in nodes
            if node.get("id") not in nodes_with_incoming
        ]
        
        inputs = {}
        for node in input_nodes:
            node_id = node.get("id")
            node_data = node.get("data", {})
            node_type = node_data.get("type")
            
            # Create input port for this node
            # In CWL, we create inputs based on node requirements
            # For simplicity, we create a generic file input
            inputs[f"{node_id}_input"] = {
                "type": "File",
                "label": f"Input for {node_id}",
            }
        
        return inputs
    
    def _node_to_cwl_step(
        self,
        node: Dict[str, Any],
        edges: List[Dict[str, Any]],
        dependencies: Dict[str, List[str]],
        tools_registry: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Convert a node to a CWL workflow step."""
        node_id = node.get("id")
        node_data = node.get("data", {})
        node_type = node_data.get("type")
        params = node_data.get("params", {})
        
        tool_info = tools_registry.get(node_type, {})
        tool_path = tool_info.get("tool_path") or node_type
        
        # Build step inputs
        step_inputs = {}
        node_deps = dependencies.get(node_id, [])
        
        for dep_node_id in node_deps:
            # Find edges connecting this dependency
            for edge in edges:
                if edge.get("source") == dep_node_id and edge.get("target") == node_id:
                    source_handle = edge.get("sourceHandle", "output")
                    target_handle = edge.get("targetHandle", "input")
                    
                    step_inputs[target_handle] = {
                        "source": f"{dep_node_id}/{source_handle}"
                    }
        
        # Add workflow-level inputs for nodes with no dependencies
        if not node_deps:
            step_inputs["input"] = f"{node_id}_input"
        
        # Build step outputs
        step_outputs = []
        tool_outputs = tool_info.get("outputs", [])
        if tool_outputs:
            for output in tool_outputs:
                output_id = output.get("id") or output.get("handle") or "output"
                step_outputs.append(output_id)
        else:
            # Default output
            step_outputs.append("output")
        
        # Build command line tool
        step = {
            "run": self._create_command_line_tool(node_id, tool_path, params, tool_info),
            "in": step_inputs,
            "out": step_outputs,
        }
        
        return step
    
    def _create_command_line_tool(
        self,
        node_id: str,
        tool_path: str,
        params: Dict[str, Any],
        tool_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an inline CommandLineTool for a step."""
        # Build base command
        base_command = tool_path
        
        # Build inputs
        inputs = []
        for param_name, param_value in params.items():
            if param_name in ("tool_type", "tool_path"):
                continue  # Skip metadata params
            
            input_spec = {
                "id": param_name,
                "type": self._infer_param_type(param_value),
            }
            
            # Add default if provided
            if param_value is not None:
                input_spec["default"] = param_value
            
            inputs.append(input_spec)
        
        # Build outputs
        outputs = []
        tool_outputs = tool_info.get("outputs", [])
        if tool_outputs:
            for output in tool_outputs:
                output_id = output.get("id") or output.get("handle") or "output"
                outputs.append({
                    "id": output_id,
                    "type": "File",
                })
        else:
            outputs.append({
                "id": "output",
                "type": "File",
            })
        
        # Build arguments (command line)
        arguments = [base_command]
        for param_name, param_value in params.items():
            if param_name in ("tool_type", "tool_path"):
                continue
            
            # Add parameter to command line
            if isinstance(param_value, bool):
                if param_value:
                    arguments.append(f"--{param_name}")
            elif param_value is not None:
                arguments.extend([f"--{param_name}", str(param_value)])
        
        cwl_tool = {
            "cwlVersion": "v1.2",
            "class": "CommandLineTool",
            "baseCommand": base_command,
            "inputs": {inp["id"]: {k: v for k, v in inp.items() if k != "id"} for inp in inputs},
            "outputs": {out["id"]: {k: v for k, v in out.items() if k != "id"} for out in outputs},
            "arguments": arguments,
        }
        
        return cwl_tool
    
    def _build_workflow_outputs(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build workflow-level outputs (nodes with no outgoing edges)."""
        # Find nodes with no outgoing edges (these are workflow outputs)
        nodes_with_outgoing = {edge.get("source") for edge in edges}
        output_nodes = [
            node for node in nodes
            if node.get("id") not in nodes_with_outgoing
        ]
        
        outputs = {}
        for node in output_nodes:
            node_id = node.get("id")
            outputs[f"{node_id}_output"] = {
                "outputSource": f"{node_id}/output",
                "type": "File",
            }
        
        return outputs
    
    def _infer_param_type(self, value: Any) -> str:
        """Infer CWL type from parameter value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "record"
        else:
            return "string"
    
    def export_to_file(
        self,
        workflow_json: Dict[str, Any],
        output_path: Path,
        tools: Optional[List[Dict[str, Any]]] = None,
        format: str = "yaml"
    ) -> None:
        """
        Export workflow to CWL file.
        
        Args:
            workflow_json: Workflow JSON from database
            output_path: Path to output file
            tools: Optional list of tool definitions
            format: Output format ("yaml" or "json")
        """
        cwl_workflow = self.export_workflow_to_cwl(workflow_json, tools)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "yaml":
            with open(output_path, "w") as f:
                yaml.dump(cwl_workflow, f, default_flow_style=False, allow_unicode=True)
        else:
            with open(output_path, "w") as f:
                json.dump(cwl_workflow, f, indent=2)

