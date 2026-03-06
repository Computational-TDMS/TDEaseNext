from app.services.workflow_service import _should_skip_node_on_resume


def test_resume_skip_returns_false_when_no_outputs_resolved():
    assert _should_skip_node_on_resume([]) is False


def test_resume_skip_returns_true_when_any_output_exists():
    class FakePath:
        def __init__(self, exists: bool):
            self._exists = exists

        def exists(self) -> bool:
            return self._exists

    assert _should_skip_node_on_resume([FakePath(True), FakePath(False)]) is True
