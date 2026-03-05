import pytest
from fastapi import HTTPException

from app.api import nodes as nodes_api


def test_validate_identifier_accepts_safe_values():
    assert nodes_api._validate_identifier("exec-1.node_2:3", "execution_id") == "exec-1.node_2:3"


def test_validate_identifier_rejects_unsafe_values():
    with pytest.raises(HTTPException) as exc:
        nodes_api._validate_identifier("../etc/passwd", "execution_id")
    assert exc.value.status_code == 400


def test_resolve_outputs_maps_value_error_to_404(monkeypatch):
    def _raise(*args, **kwargs):
        raise ValueError("Execution not found: exec1")

    monkeypatch.setattr(nodes_api, "resolve_node_outputs", _raise)

    with pytest.raises(HTTPException) as exc:
        nodes_api._resolve_outputs_or_http("exec1", "node1", object())
    assert exc.value.status_code == 404

