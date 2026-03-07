from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api import execution as execution_api
from app.api import workflow as workflow_api
from app.core.executor.errors import WorkspaceValidationError


def test_workflow_public_error_mapping_uses_stable_code():
    public_error = workflow_api._public_execution_error(WorkspaceValidationError("workspace invalid"))
    assert public_error.code == "WORKSPACE_INVALID"
    assert public_error.status_code == 400


def test_workflow_redacted_payload_contains_correlation_id():
    with pytest.raises(HTTPException) as exc_info:
        workflow_api._raise_sanitized_execution_http_error(
            "Execute",
            RuntimeError("sensitive internal failure detail"),
        )
    payload = exc_info.value.detail
    assert payload["code"] == "EXECUTION_INTERNAL_ERROR"
    assert "correlation_id" in payload
    assert "sensitive internal failure detail" not in payload["message"]


def test_execution_redacted_payload_contains_correlation_id():
    with pytest.raises(HTTPException) as exc_info:
        execution_api._raise_sanitized_execution_http_error(
            "Get node data",
            RuntimeError("secret stack detail"),
        )
    payload = exc_info.value.detail
    assert payload["code"] == "EXECUTION_INTERNAL_ERROR"
    assert "correlation_id" in payload
    assert "secret stack detail" not in payload["message"]
