from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ExecutionPublicError:
    code: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None

    def to_payload(self, correlation_id: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "correlation_id": correlation_id,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ExecutorError(RuntimeError):
    public_error = ExecutionPublicError(
        code="EXECUTION_INTERNAL_ERROR",
        message="Execution failed.",
        status_code=500,
    )

    def to_public_error(self) -> ExecutionPublicError:
        return self.public_error


class LaunchValidationError(ExecutorError):
    public_error = ExecutionPublicError(
        code="EXECUTION_LAUNCH_INVALID",
        message="Execution launch contract is invalid.",
        status_code=400,
    )


class ExecutableNotFoundError(LaunchValidationError):
    public_error = ExecutionPublicError(
        code="EXECUTABLE_NOT_FOUND",
        message="Executable for this task cannot be resolved.",
        status_code=400,
    )


class WorkspaceValidationError(LaunchValidationError):
    public_error = ExecutionPublicError(
        code="WORKSPACE_INVALID",
        message="Workspace path is invalid for execution.",
        status_code=400,
    )


class CommandExecutionError(ExecutorError):
    public_error = ExecutionPublicError(
        code="EXECUTION_FAILED",
        message="Process execution failed.",
        status_code=500,
    )
