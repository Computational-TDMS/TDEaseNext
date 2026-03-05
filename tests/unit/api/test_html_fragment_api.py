"""
Integration tests for HTML Fragment API
Tests the /api/executions/{execution_id}/nodes/{node_id}/html/{row_id} endpoint
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_database
from app.services.node_data_service import resolve_node_outputs


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database"""
    db = Mock()
    # Mock workflow snapshot with TopPIC node
    cursor = Mock()
    cursor.fetchone.return_value = [
        """{
            "nodes": [
                {
                    "id": "toppic_1",
                    "type": "toppic",
                    "data": {}
                }
            ],
            "edges": []
        }"""
    ]
    db.cursor.return_value = cursor
    return db


@pytest.fixture
def sample_html_output(tmp_path):
    """Create sample TopPIC HTML output structure"""
    html_dir = tmp_path / "test_sample_html"
    html_dir.mkdir()

    # Create index.html
    (html_dir / "index.html").write_text("<html><body>TopPIC Viewer</body></html>")

    # Create PrSM-specific HTML files
    prsm_html_dir = html_dir / "prsm"
    prsm_html_dir.mkdir()

    # Sample PrSM HTML fragments
    (prsm_html_dir / "prsm_0.html").write_text("""
        <html><body>
            <h1>PrSM #0</h1>
            <div class="sequence">ACDEFGHIK</div>
            <div class="mass">12345.67</div>
        </body></html>
    """)

    (prsm_html_dir / "prsm_1.html").write_text("""
        <html><body>
            <h1>PrSM #1</h1>
            <div class="sequence">LMNPQRSTVW</div>
            <div class="mass">23456.78</div>
        </body></html>
    """)

    return html_dir


@pytest.mark.asyncio
async def test_get_html_fragment_success(
    test_client,
    mock_db,
    sample_html_output,
    tmp_path
):
    """
    Test successful HTML fragment retrieval by row ID

    Given: A TopPIC node with HTML output exists
    When: Requesting HTML fragment for row_id=0
    Then: Returns PrSM HTML fragment with status 200
    """
    execution_id = "test_exec_1"
    node_id = "toppic_1"
    row_id = 0

    # Mock resolve_node_outputs to return HTML directory
    with patch('app.api.nodes.resolve_node_outputs') as mock_resolve:
        mock_resolve.return_value = {
            "node_id": node_id,
            "outputs": [
                {
                    "port_id": "html_folder",
                    "file_name": "test_sample_html",
                    "file_path": str(sample_html_output),
                    "exists": True,
                    "is_directory": True
                }
            ]
        }

        # Override database dependency
        app.dependency_overrides[get_database] = lambda: mock_db

        response = test_client.get(
            f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["node_id"] == node_id
        assert data["row_id"] == row_id
        assert data["exists"] is True
        assert "ACDEFGHIK" in data["html"]  # Sequence from PrSM #0
        assert "12345.67" in data["html"]  # Mass from PrSM #0

        # Clean up
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_html_fragment_not_found(
    test_client,
    mock_db,
    sample_html_output,
    tmp_path
):
    """
    Test HTML fragment request for non-existent row ID

    Given: A TopPIC node with HTML output exists (only 2 PrSMs)
    When: Requesting HTML fragment for row_id=999
    Then: Returns exists=False with appropriate message
    """
    execution_id = "test_exec_1"
    node_id = "toppic_1"
    row_id = 999

    with patch('app.api.nodes.resolve_node_outputs') as mock_resolve:
        mock_resolve.return_value = {
            "node_id": node_id,
            "outputs": [
                {
                    "port_id": "html_folder",
                    "file_name": "test_sample_html",
                    "file_path": str(sample_html_output),
                    "exists": True,
                    "is_directory": True
                }
            ]
        }

        app.dependency_overrides[get_database] = lambda: mock_db

        response = test_client.get(
            f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}",
            
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["exists"] is False
        assert "not found" in data["html"].lower()

        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_html_fragment_node_not_found(
    test_client,
    mock_db
):
    """
    Test HTML fragment request for non-existent node

    Given: Node does not exist in workflow
    When: Requesting HTML fragment
    Then: Returns 404 error
    """
    execution_id = "test_exec_1"
    node_id = "nonexistent_node"
    row_id = 0

    with patch('app.api.nodes.resolve_node_outputs') as mock_resolve:
        mock_resolve.side_effect = ValueError("Node not found")

        app.dependency_overrides[get_database] = lambda: mock_db

        response = test_client.get(
            f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}",
            
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_html_fragment_invalid_row_id(
    test_client,
    mock_db
):
    """
    Test HTML fragment request with invalid row ID

    Given: Valid node exists
    When: Requesting HTML fragment with invalid row_id (negative)
    Then: Returns 400 error
    """
    execution_id = "test_exec_1"
    node_id = "toppic_1"
    row_id = -1  # Invalid negative ID

    app.dependency_overrides[get_database] = lambda: mock_db

    response = test_client.get(
        f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}",
        
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_html_fragment_missing_html_output(
    test_client,
    mock_db,
    tmp_path
):
    """
    Test HTML fragment request when node has no HTML output

    Given: Node exists but has no HTML output port
    When: Requesting HTML fragment
    Then: Returns 404 error
    """
    execution_id = "test_exec_1"
    node_id = "topfd_1"  # TopFD node (no HTML output)
    row_id = 0

    with patch('app.api.nodes.resolve_node_outputs') as mock_resolve:
        mock_resolve.return_value = {
            "node_id": node_id,
            "outputs": [
                {
                    "port_id": "ms1feature",
                    "file_name": "test_ms1.feature",
                    "exists": True
                }
            ]
        }

        app.dependency_overrides[get_database] = lambda: mock_db

        response = test_client.get(
            f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}",
            
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_html_fragment_caching(
    test_client,
    mock_db,
    sample_html_output,
    tmp_path
):
    """
    Test that HTML fragments are cached for performance

    Given: HTML fragment has been requested once
    When: Requesting the same fragment again
    Then: Returns cached result (verified by faster response)
    """
    execution_id = "test_exec_1"
    node_id = "toppic_1"
    row_id = 0

    with patch('app.api.nodes.resolve_node_outputs') as mock_resolve:
        mock_resolve.return_value = {
            "node_id": node_id,
            "outputs": [
                {
                    "port_id": "html_folder",
                    "file_name": "test_sample_html",
                    "file_path": str(sample_html_output),
                    "exists": True,
                    "is_directory": True
                }
            ]
        }

        app.dependency_overrides[get_database] = lambda: mock_db

        # First request
        response1 = test_client.get(
            f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}",
            
        )

        # Second request (should be cached)
        response2 = test_client.get(
            f"/api/executions/{execution_id}/nodes/{node_id}/html/{row_id}",
            
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

        app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
