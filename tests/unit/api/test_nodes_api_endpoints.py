import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api import nodes as nodes_api


@pytest.mark.asyncio
async def test_get_rows_rejects_invalid_execution_id():
    with pytest.raises(HTTPException) as exc:
        await nodes_api.get_node_data_rows(
            execution_id="../bad",
            node_id="node1",
            offset=0,
            limit=10,
            row_ids=None,
            db=object(),
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_rows_rejects_negative_row_ids(monkeypatch):
    monkeypatch.setattr(
        nodes_api,
        "_resolve_outputs_or_http",
        lambda execution_id, node_id, db: {
            "outputs": [
                {
                    "port_id": "output",
                    "file_name": "test.tsv",
                    "file_path": "test.tsv",
                    "exists": True,
                    "parseable": True,
                }
            ]
        },
    )

    with pytest.raises(HTTPException) as exc:
        await nodes_api.get_node_data_rows(
            execution_id="exec1",
            node_id="node1",
            offset=0,
            limit=10,
            row_ids="-1,2",
            db=object(),
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_rows_limits_file_read_to_max_requested_index(monkeypatch):
    requested = {}

    monkeypatch.setattr(
        nodes_api,
        "_resolve_outputs_or_http",
        lambda execution_id, node_id, db: {
            "outputs": [
                {
                    "port_id": "output",
                    "file_name": "test.tsv",
                    "file_path": "test.tsv",
                    "exists": True,
                    "parseable": True,
                }
            ]
        },
    )

    def fake_parse(file_path: Path, max_rows=None):
        requested["max_rows"] = max_rows
        return {
            "columns": ["id"],
            "rows": [{"id": str(i)} for i in range(6)],
            "total_rows": 6,
        }

    monkeypatch.setattr(nodes_api, "parse_tabular_file", fake_parse)

    response = await nodes_api.get_node_data_rows(
        execution_id="exec1",
        node_id="node1",
        offset=0,
        limit=10,
        row_ids="1,3,5",
        db=object(),
    )
    payload = json.loads(response.body)

    assert requested["max_rows"] == 6
    assert [row["id"] for row in payload["rows"]] == ["1", "3", "5"]

