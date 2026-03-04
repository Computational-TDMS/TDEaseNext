"""
Tool registry and management data models
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class ToolParameter(BaseModel):
    """Tool parameter definition"""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (value, boolean, choice)")
    flag: str = Field(..., description="Command line flag")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(False, description="Whether parameter is required")
    default_value: Optional[Any] = Field(None, description="Default parameter value")
    choices: Optional[Dict[str, str]] = Field(None, description="Choices for choice type parameters")


class ToolOutputPattern(BaseModel):
    """Tool output file pattern definition"""

    pattern: str = Field(..., description="Output file pattern")
    handle: str = Field(..., description="Output handle identifier")
    description: Optional[str] = Field(None, description="Pattern description")


class ToolInfo(BaseModel):
    """Complete tool information model"""

    tool_type: str = Field(..., description="Tool type identifier")
    description: str = Field(..., description="Tool description")
    tool_type_category: str = Field(..., description="Tool type (command or script)")
    tool_path: str = Field(..., description="Tool executable or script path")
    input_params: List[str] = Field(..., description="Expected input parameter names")
    output_patterns: List[ToolOutputPattern] = Field(..., description="Output file patterns")
    param_mapping: Dict[str, ToolParameter] = Field(..., description="Parameter to flag mapping")
    conda_env: Optional[str] = Field(None, description="Conda environment file path")
    is_available: bool = Field(False, description="Tool availability status")
    platform: str = Field(..., description="Supported platform (windows, linux, both)")
    version: Optional[str] = Field(None, description="Tool version if known")
    last_validated: Optional[datetime] = Field(None, description="Last validation timestamp")
    positional_params: Optional[List[str]] = Field(None, description="Positional parameter names")
    output_flag_supported: bool = Field(True, description="Whether tool supports output directory flag")

class ToolRegistration(BaseModel):
    """Model for registering a new tool"""

    tool_type: str = Field(..., min_length=1, max_length=50, description="Tool type identifier")
    description: str = Field(..., max_length=500, description="Tool description")
    tool_type_category: str = Field(..., pattern="^(command|script)$", description="Tool type")
    tool_path: str = Field(..., description="Tool executable or script path")
    input_params: List[str] = Field(default_factory=list, description="Expected input parameter names")
    output_patterns: List[Dict[str, str]] = Field(default_factory=list, description="Output patterns as dicts")
    param_mapping: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Parameter mapping")
    conda_env: Optional[str] = Field(None, description="Conda environment file path")
    platform: str = Field("both", pattern="^(windows|linux|both)$", description="Supported platform")
    positional_params: Optional[List[str]] = Field(None, description="Positional parameter names")
    output_flag_supported: bool = Field(True, description="Support for output directory flag")

    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Tool type is required")
        return v.strip()

    @field_validator("tool_path")
    @classmethod
    def validate_tool_path(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Tool path is required")
        return v.strip()


class ToolValidationResult(BaseModel):
    """Result of tool availability validation"""

    tool_type: str = Field(..., description="Tool type identifier")
    is_available: bool = Field(..., description="Whether tool is available")
    found_paths: List[str] = Field(default_factory=list, description="Discovered tool paths")
    validation_message: Optional[str] = Field(None, description="Validation result message")
    version_info: Optional[str] = Field(None, description="Tool version if available")
    validation_time: datetime = Field(..., description="Validation timestamp")

class ToolSchema(BaseModel):
    """JSON schema for tool parameters"""

    tool_type: str = Field(..., description="Tool type identifier")
    tool_schema: Dict[str, Any] = Field(..., description="JSON schema for tool parameters", alias="schema")
    examples: Optional[Dict[str, Any]] = Field(None, description="Example parameter values")


class ToolDiscoveryRequest(BaseModel):
    """Request for tool discovery"""

    tool_types: Optional[List[str]] = Field(None, description="Specific tool types to discover")
    refresh_cache: bool = Field(False, description="Whether to refresh tool cache")
    platform_filter: Optional[str] = Field(None, pattern="^(windows|linux|both|current)$",
                                         description="Filter by platform")


class ToolListResponse(BaseModel):
    """Response model for tool list"""

    tools: Dict[str, ToolInfo] = Field(..., description="Available tools by type")
    total_count: int = Field(..., description="Total number of tools")
    available_count: int = Field(..., description="Number of available tools")
    platform: str = Field(..., description="Current platform")
    cache_timestamp: Optional[datetime] = Field(None, description="Cache generation time")

