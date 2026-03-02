from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ToolParam(BaseModel):
    id: str
    name: str
    type: str
    default: Optional[Any] = None
    options: Optional[List[Dict[str, Any]]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    precision: Optional[int] = None
    description: Optional[str] = None

class ToolPort(BaseModel):
    id: str
    name: str
    type: str
    required: Optional[bool] = False
    description: Optional[str] = None
    pattern: Optional[str] = None
    handle: Optional[str] = None
    accept: Optional[List[str]] = None
    provides: Optional[List[str]] = None

class DockerConfig(BaseModel):
    image: Optional[str] = None
    commandPrefix: Optional[str] = None
    volumeMountStrategy: Optional[str] = "workspace"
    volumeMountTemplate: Optional[str] = None
    workingDir: Optional[str] = "/data"

class ToolConfig(BaseModel):
    id: str
    name: str
    kind: str
    description: Optional[str] = None
    toolPath: Optional[str] = None
    executionMode: Optional[str] = "native"
    params: Optional[List[ToolParam]] = None
    inputs: Optional[List[ToolPort]] = None
    outputs: Optional[List[ToolPort]] = None
    positionalParams: Optional[List[str]] = None
    paramMapping: Optional[Dict[str, Dict[str, Any]]] = None
    outputFlag: Optional[str] = None
    outputFlagSupported: Optional[bool] = True
    docker: Optional[DockerConfig] = None

class Position(BaseModel):
    x: float
    y: float

class NodeDefinition(BaseModel):
    id: str
    type: str
    position: Position
    displayProperties: Dict[str, Any]
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    nodeConfig: Dict[str, Any]

class ConnectionEnd(BaseModel):
    nodeId: str
    portId: str

class ConnectionDefinition(BaseModel):
    id: str
    source: ConnectionEnd
    target: ConnectionEnd
    dataPath: Optional[Dict[str, Optional[str]]] = None

class WorkflowMetadata(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    created: str
    modified: str
    tags: Optional[List[str]] = Field(default_factory=list)
    uuid: Optional[str] = None
    license: Optional[str] = None
    creator: Optional[List[Dict[str, Any]]] = None

class WorkflowStepInput(BaseModel):
    """Galaxy format step input definition"""
    source: str  # Reference to step output (e.g., "step_name/output_name") or workflow input

class WorkflowStepOutput(BaseModel):
    """Galaxy format step output definition"""
    outputSource: Optional[str] = None  # Reference to step output (e.g., "step_name/output_name")

class WorkflowStep(BaseModel):
    """Galaxy format workflow step definition"""
    id: str  # Step ID (usually matches node ID)
    type: str  # Step type: "tool", "data_input", "data_collection_input", "subworkflow", etc.
    tool_id: Optional[str] = None  # Tool identifier for tool steps
    tool_state: Optional[Dict[str, Any]] = None  # Tool parameter values
    inputs: Optional[Dict[str, Any]] = None  # Step inputs mapping
    outputs: Optional[Dict[str, str]] = None  # Step outputs mapping
    position: Optional[Dict[str, float]] = None  # Step position in workflow

class WorkflowInput(BaseModel):
    """Galaxy format workflow input definition"""
    id: str
    type: str  # Usually "data"
    label: Optional[str] = None

class WorkflowOutput(BaseModel):
    """Galaxy format workflow output definition"""
    id: str
    outputSource: str  # Reference to step output (e.g., "step_name/output_name")
    label: Optional[str] = None

class WorkflowJSON(BaseModel):
    metadata: WorkflowMetadata
    format_version: Optional[str] = Field(default="2.0", alias="format-version")
    nodes: List[NodeDefinition]  # VueFlow UI nodes (for rendering)
    connections: List[ConnectionDefinition]  # VueFlow connections (for rendering)
    steps: Optional[Dict[str, WorkflowStep]] = None  # Galaxy format steps (for execution)
    inputs: Optional[Dict[str, WorkflowInput]] = None  # Galaxy format workflow inputs
    outputs: Optional[Dict[str, WorkflowOutput]] = None  # Galaxy format workflow outputs
    projectSettings: Dict[str, Any]
    
    class Config:
        populate_by_name = True

class ExecuteRequest(BaseModel):
    workflow: WorkflowJSON
    tools: List[ToolConfig]
    parameters: Optional[Dict[str, Any]] = None

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

class NodeStatus(BaseModel):
    """Node execution status"""
    node_id: str
    rule_name: Optional[str] = None
    status: str
    progress: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_message: Optional[str] = None

class WorkflowExecutionResponse(BaseModel):
    executionId: str
    status: str
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    progress: int = 0
    logs: List[LogEntry] = Field(default_factory=list)
    nodes: Optional[List[NodeStatus]] = Field(default_factory=list)
    results: Optional[Dict[str, Any]] = None

class BatchSample(BaseModel):
    """Batch processing sample configuration"""
    sample_id: str = Field(..., description="Sample ID/name")
    placeholder_values: Dict[str, Any] = Field(default_factory=dict, description="Placeholder variable values (e.g., {sample}, {fasta_file})")

class BatchConfig(BaseModel):
    """Batch processing configuration"""
    samples: List[BatchSample] = Field(default_factory=list, description="List of samples for batch processing")
    global_params: Optional[Dict[str, Any]] = Field(None, description="Global parameters that override workflow-level parameters")
