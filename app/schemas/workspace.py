"""
Workspace and Sample Management Schemas

Pydantic models for workspace and sample data structures.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    """User settings"""
    default_workspace: Optional[str] = None
    max_workspaces: int = 10
    max_executions_per_workspace: int = 100


class UserMetadata(BaseModel):
    """User metadata"""
    user_id: str
    username: str
    email: Optional[str] = ""
    display_name: Optional[str] = ""
    created_at: str
    updated_at: str
    settings: UserSettings = Field(default_factory=UserSettings)


class WorkspaceSettings(BaseModel):
    """Workspace settings"""
    max_samples: int = 1000
    retention_days: int = 30
    auto_cleanup: bool = True


class WorkspaceStatistics(BaseModel):
    """Workspace statistics"""
    total_samples: int = 0
    total_workflows: int = 0
    total_executions: int = 0


class WorkspaceMetadata(BaseModel):
    """Workspace metadata"""
    workspace_id: str
    name: str
    description: str = ""
    owner: str
    created_at: str
    updated_at: str
    settings: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    statistics: WorkspaceStatistics = Field(default_factory=WorkspaceStatistics)


class SampleDefinition(BaseModel):
    """Sample definition"""
    id: str
    name: str
    description: str = ""
    context: Dict[str, str] = Field(default_factory=dict)
    data_paths: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class SamplesFile(BaseModel):
    """Samples.json file structure"""
    version: str = "1.0"
    workspace_id: str
    created_at: str
    updated_at: str
    samples: Dict[str, SampleDefinition] = Field(default_factory=dict)


class SampleCreate(BaseModel):
    """Request to create a new sample"""
    id: str = Field(..., description="Unique sample identifier")
    name: str = Field(..., description="Display name")
    description: str = Field("", description="Sample description")
    context: Dict[str, str] = Field(default_factory=dict, description="Placeholder values")
    data_paths: Dict[str, str] = Field(default_factory=dict, description="File path templates")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SampleUpdate(BaseModel):
    """Request to update a sample"""
    name: Optional[str] = None
    description: Optional[str] = None
    context: Optional[Dict[str, str]] = None
    data_paths: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkspaceCreate(BaseModel):
    """Request to create a new workspace"""
    workspace_id: str = Field(..., description="Unique workspace identifier")
    name: str = Field(..., description="Workspace name")
    description: str = Field("", description="Workspace description")


class ExecutionMetadata(BaseModel):
    """Execution metadata"""
    execution_id: str
    workspace_id: str
    workflow_id: Optional[str] = None
    samples: List[str] = Field(default_factory=list)
    status: str = "created"
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
