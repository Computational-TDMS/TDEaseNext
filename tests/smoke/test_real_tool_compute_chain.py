from __future__ import annotations

from pathlib import Path

import pytest

from app.services.tool_registry import get_tool_registry
from app.services.workflow_service import WorkflowService
from tests.helpers.prod_smoke_prereqs import detect_prod_smoke_prereqs

pytestmark = pytest.mark.prod_smoke


def _build_workflow(mzml_path: Path, fasta_path: Path) -> dict:
    return {
        "metadata": {
            "id": "wf_prod_smoke_real_tools",
            "name": "Prod Smoke: DataLoader -> TopFD -> TopPIC",
        },
        "format_version": "2.0",
        "nodes": [
            {
                "id": "data_loader_1",
                "type": "tool",
                "data": {
                    "type": "data_loader",
                    "params": {
                        "input_sources": [str(mzml_path)],
                    },
                },
            },
            {
                "id": "fasta_loader_1",
                "type": "tool",
                "data": {
                    "type": "fasta_loader",
                    "params": {
                        "fasta_file": str(fasta_path),
                    },
                },
            },
            {
                "id": "topfd_1",
                "type": "tool",
                "data": {
                    "type": "topfd",
                    "params": {
                        "thread_number": "1",
                        "skip_html_folder": True,
                    },
                },
            },
            {
                "id": "toppic_1",
                "type": "tool",
                "data": {
                    "type": "toppic",
                    "params": {
                        "thread_number": "1",
                        "skip_html_folder": True,
                    },
                },
            },
        ],
        "edges": [
            {
                "id": "e_loader_topfd",
                "source": "data_loader_1",
                "target": "topfd_1",
                "sourceHandle": "output-mzml",
                "targetHandle": "input-input_files",
            },
            {
                "id": "e_topfd_toppic",
                "source": "topfd_1",
                "target": "toppic_1",
                "sourceHandle": "output-ms2_msalign",
                "targetHandle": "input-msalign_files",
            },
            {
                "id": "e_fasta_toppic",
                "source": "fasta_loader_1",
                "target": "toppic_1",
                "sourceHandle": "output-fasta",
                "targetHandle": "input-fasta_file",
            },
        ],
    }


@pytest.mark.asyncio
async def test_prod_smoke_real_compute_chain(tmp_path: Path) -> None:
    prereqs = detect_prod_smoke_prereqs()
    if not prereqs.ready:
        pytest.skip(prereqs.skip_reason())

    assert prereqs.mzml_fixture is not None
    assert prereqs.fasta_fixture is not None

    sample_name = prereqs.mzml_fixture.stem
    fasta_name = prereqs.fasta_fixture.stem
    workflow = _build_workflow(prereqs.mzml_fixture, prereqs.fasta_fixture)

    workspace = tmp_path / "prod_smoke_workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    workflow_service = WorkflowService(tool_registry=get_tool_registry())
    result = await workflow_service.execute_workflow(
        workflow_json=workflow,
        workspace_path=workspace,
        parameters={
            "sample": sample_name,
            "sample_context": {
                "sample": sample_name,
                "fasta_filename": fasta_name,
            },
            "resume": False,
            "simulate": False,
            "dryrun": False,
        },
        dryrun=False,
        simulate=False,
        resume=False,
    )

    assert result["status"] == "completed", result

    topfd_output = workspace / f"{sample_name}_ms2.msalign"
    toppic_output = workspace / f"{sample_name}_ms2_toppic_prsm_single.tsv"

    assert topfd_output.exists(), f"TopFD output missing: {topfd_output}"
    assert toppic_output.exists(), f"TopPIC output missing: {toppic_output}"
