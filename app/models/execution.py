"""
Workflow execution-related data models
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime


class ExecutionRequest(BaseModel):
    """Model for starting workflow execution"""

    user_id: str = Field(..., description="User identifier")
    workspace_id: str = Field(..., description="Workspace identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    sample_ids: Optional[List[str]] = Field(None, description="Sample IDs for execution (from samples.json)")
    params: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")
    cores: int = Field(4, ge=1, le=32, description="Number of CPU cores to use")
    use_conda: bool = Field(True, description="Whether to use conda environments")
    dry_run: bool = Field(False, description="Whether to do a dry run (no actual execution)")
    force_restart: bool = Field(False, description="Whether to force restart if already running")
    engine_args: Optional[Dict[str, Any]] = Field(None, description="Additional engine arguments")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides for execution")
    environment: Optional[Dict[str, Any]] = Field(None, description="Environment variables for execution")

    @field_validator("workflow_id")
    @classmethod
    def validate_workflow_id(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Workflow ID is required")
        return v.strip()

    @field_validator("sample_ids")
    @classmethod
    def validate_sample_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """If sample_ids is None, will load all samples from workspace"""
        return v  # Validation will happen in execution service


class ExecutionResponse(BaseModel):
    """Response model for execution request"""

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., pattern="^(pending|starting|running|completed|failed|cancelled|paused)$",
                     description="Execution status")
    message: str = Field(..., description="Execution status message")
    start_time: Optional[datetime] = Field(None, description="Execution start time")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")

class ExecutionStatus(BaseModel):
    """Detailed execution status model"""

    execution_id: str = Field(..., description="Execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., pattern="^(pending|starting|running|completed|failed|cancelled|paused)$",
                     description="Current execution status")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    current_node_id: Optional[str] = Field(None, description="Currently executing node ID")
    total_rules: Optional[int] = Field(None, description="Total number of rules")
    completed_rules: Optional[int] = Field(None, description="Number of completed rules")
    failed_rules: Optional[int] = Field(None, description="Number of failed rules")
    start_time: datetime = Field(..., description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    return_code: Optional[int] = Field(None, description="Process return code")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    cores_used: Optional[int] = Field(None, description="Number of CPU cores used")
    memory_usage: Optional[int] = Field(None, description="Memory usage in MB")
    log_lines: Optional[List[str]] = Field(None, description="Recent log lines")

class ExecutionListItem(BaseModel):
    """Simplified execution model for list views"""

    execution_id: str = Field(..., description="Execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    workflow_name: Optional[str] = Field(None, description="Workflow name")
    status: str = Field(..., description="Execution status")
    start_time: datetime = Field(..., description="Execution start time")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    cores_used: int = Field(..., description="CPU cores used")
    sample_count: Optional[int] = Field(None, description="Number of samples")

class ExecutionStopRequest(BaseModel):
    """Request for stopping execution"""

    execution_id: str = Field(..., description="Execution identifier")
    force: bool = Field(False, description="Whether to force stop immediately")
    cleanup: bool = Field(True, description="Whether to cleanup temporary files")

    @field_validator("execution_id")
    @classmethod
    def validate_execution_id(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Execution ID is required")
        return v.strip()


class LogRequest(BaseModel):
    """Request for execution logs"""

    execution_id: str = Field(..., description="Execution identifier")
    lines: int = Field(100, ge=1, le=10000, description="Number of lines to retrieve")
    offset: int = Field(0, ge=0, description="Line offset")
    level: Optional[str] = Field(None, pattern="^(debug|info|warning|error|all)$",
                                 description="Log level filter")

    @field_validator("execution_id")
    @classmethod
    def validate_execution_id(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Execution ID is required")
        return v.strip()


class LogResponse(BaseModel):
    """Response model for log request"""

    execution_id: str = Field(..., description="Execution identifier")
    log_lines: List[str] = Field(..., description="Log lines")
    total_lines: int = Field(..., description="Total lines in log file")
    has_more: bool = Field(..., description="Whether more lines are available")
    log_file_path: Optional[str] = Field(None, description="Path to log file")


class ExecutionMetrics(BaseModel):
    """Execution performance metrics"""

    execution_id: str = Field(..., description="Execution identifier")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    memory_usage: Optional[int] = Field(None, description="Memory usage in MB")
    disk_usage: Optional[int] = Field(None, description="Disk usage in MB")
    io_read: Optional[int] = Field(None, description="Bytes read")
    io_write: Optional[int] = Field(None, description="Bytes written")
    network_io: Optional[int] = Field(None, description="Network I/O bytes")
    timestamp: datetime = Field(..., description="Metrics timestamp")

