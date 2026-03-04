"""
Workflow-related data models
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class WorkflowValidation(BaseModel):
    """Model for workflow validation results"""

    valid: bool = Field(..., description="Whether workflow is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    generated_files: List[str] = Field(default_factory=list, description="List of generated files")
    compilation_time: Optional[float] = Field(None, description="Compilation time in seconds")
    error_details: List[Dict[str, Any]] = Field(default_factory=list, description="Structured error details")


class WorkflowCreate(BaseModel):
    """Model for creating a new workflow from VueFlow JSON"""

    name: str = Field(..., min_length=1, max_length=100, description="Workflow name")
    description: Optional[str] = Field(None, max_length=500, description="Workflow description")
    vueflow_data: Dict[str, Any] = Field(..., description="VueFlow JSON data structure")
    workspace_path: str = Field(..., description="User-provided workspace directory path")
    samples: Optional[List[str]] = Field(None, description="Sample list for workflow execution")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional workflow metadata")

    @field_validator("workspace_path")
    @classmethod
    def validate_workspace_path(cls, v: str) -> str:
        """Validate that workspace path is provided and not empty"""
        if not v or v.strip() == "":
            raise ValueError("Workspace path is required")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workflow name"""
        if not v or v.strip() == "":
            raise ValueError("Workflow name is required")
        return v.strip()


class WorkflowResponse(BaseModel):
    """Model for workflow response with status and metadata"""

    id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    status: str = Field(..., pattern="^(created|compiling|compiled|executing|completed|failed|error)$",
                     description="Current workflow status")
    workspace_path: str = Field(..., description="Path to user workspace directory")
    created_at: datetime = Field(..., description="Workflow creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    vueflow_data: Dict[str, Any] = Field(default_factory=dict, description="VueFlow JSON data structure")

    # Optional fields that may not be present immediately
    config_path: Optional[str] = Field(None, description="Path to generated config file")
    snakefile_path: Optional[str] = Field(None, description="Path to generated Snakefile")
    vueflow_file: Optional[str] = Field(None, description="Path to stored VueFlow JSON file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Workflow metadata")

class WorkflowListResponse(BaseModel):
    workflows: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int

class WorkflowCompilationRequest(BaseModel):
    """Model for workflow compilation request"""

    vueflow_data: Dict[str, Any] = Field(..., description="VueFlow JSON data")
    workflow_name: str = Field(..., description="Name for the workflow")
    workspace_path: str = Field(..., description="Target workspace directory")
    samples: Optional[List[str]] = Field(None, description="Sample names for workflow")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class WorkflowUpdate(BaseModel):
    """Model for updating workflow parameters"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    samples: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    vueflow_data: Optional[Dict[str, Any]] = Field(None, description="VueFlow JSON data structure")
    workspace_path: Optional[str] = Field(None, description="Workspace directory path")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            raise ValueError("Name cannot be empty if provided")
        return v.strip() if v else v


class WorkflowStatus(BaseModel):
    workflow_id: str = Field(...)
    status: str = Field(...)
    engine_status: Dict[str, Any] = Field(default_factory=dict, description="Engine execution status")
    last_updated: datetime = Field(...)

class WorkflowImportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    workspace_path: str = Field(...)
    document: str = Field(..., description="Galaxy workflow document (.ga JSON or .gxwf YAML/JSON)")
    metadata: Optional[Dict[str, Any]] = Field(None)


class WorkflowListItem(BaseModel):
    """Model for workflow list items (simplified view)"""

    id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    workspace_path: str = Field(..., description="Workspace directory")

