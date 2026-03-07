from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from app.services.workflow_service import _should_skip_node_on_resume


class _FakePath:
    def __init__(self, exists: bool):
        self._exists = exists

    def exists(self) -> bool:
        return self._exists


def _make_tmp_dir() -> Path:
    base = Path("data") / "test_tmp_dirs"
    base.mkdir(parents=True, exist_ok=True)
    path = (base / f"resume_check_{uuid4().hex}").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_resume_skip_returns_false_when_no_outputs_resolved():
    assert _should_skip_node_on_resume([], required_output_paths=[]) is False


def test_resume_skip_returns_false_when_only_partial_required_outputs_exist():
    required = [_FakePath(True), _FakePath(False)]
    assert _should_skip_node_on_resume(required, required_output_paths=required) is False


def test_resume_skip_returns_true_when_all_required_outputs_exist():
    required = [_FakePath(True), _FakePath(True)]
    assert _should_skip_node_on_resume(required, required_output_paths=required) is True


def test_resume_skip_can_ignore_missing_optional_outputs():
    all_outputs = [_FakePath(True), _FakePath(False)]
    required_outputs = [_FakePath(True)]
    assert _should_skip_node_on_resume(all_outputs, required_output_paths=required_outputs) is True


def test_resume_skip_uses_manifest_required_outputs():
    tmp_dir = _make_tmp_dir()
    required = tmp_dir / "required.txt"
    required.write_text("ok", encoding="utf-8")
    optional = tmp_dir / "optional.txt"
    manifest = tmp_dir / "node.json"
    manifest.write_text(
        json.dumps(
            {
                "node_id": "n1",
                "completed": True,
                "required_outputs": [str(required)],
                "all_outputs": [str(required), str(optional)],
            }
        ),
        encoding="utf-8",
    )

    assert _should_skip_node_on_resume(
        [required, optional],
        required_output_paths=[required, optional],
        completion_manifest=manifest,
    ) is True
