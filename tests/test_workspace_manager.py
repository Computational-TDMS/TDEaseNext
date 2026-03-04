"""
Test script for UnifiedWorkspaceManager

This script tests the new hierarchical workspace structure:
- Users → Workspaces → Samples/Workflows/Executions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.unified_workspace_manager import get_unified_workspace_manager
import json


def test_workspace_manager():
    """Test workspace manager functionality"""

    print("=" * 60)
    print("Testing UnifiedWorkspaceManager")
    print("=" * 60)

    # Initialize manager
    manager = get_unified_workspace_manager("data")

    # Test 1: Check if test user exists
    print("\n1. Checking test user...")
    user_path = manager.get_user_path("test_user")
    print(f"   User path: {user_path}")
    print(f"   Exists: {user_path.exists()}")

    # Load user metadata
    if user_path.exists():
        with open(user_path / "user.json", 'r') as f:
            user_meta = json.load(f)
        print(f"   User: {user_meta['username']}")
        print(f"   Email: {user_meta['email']}")

    # Test 2: Check workspace
    print("\n2. Checking test workspace...")
    workspace_path = manager.get_workspace_path("test_user", "test_workspace")
    print(f"   Workspace path: {workspace_path}")
    print(f"   Exists: {workspace_path.exists()}")

    # Load workspace metadata
    if workspace_path.exists():
        with open(workspace_path / "workspace.json", 'r') as f:
            workspace_meta = json.load(f)
        print(f"   Workspace: {workspace_meta['name']}")
        print(f"   Description: {workspace_meta['description']}")
        print(f"   Statistics: {workspace_meta['statistics']}")

    # Test 3: Load samples
    print("\n3. Loading samples...")
    samples_data = manager.load_samples("test_user", "test_workspace")
    samples = samples_data.get("samples", {})
    print(f"   Total samples: {len(samples)}")

    for sample_id, sample in samples.items():
        print(f"\n   Sample: {sample_id}")
        print(f"   Name: {sample['name']}")
        print(f"   Context: {sample['context']}")
        print(f"   Data paths: {list(sample['data_paths'].keys())}")

    # Test 4: Get sample context
    print("\n4. Testing sample context retrieval...")
    if samples:
        first_sample_id = list(samples.keys())[0]
        context = manager.get_sample_context("test_user", "test_workspace", first_sample_id)
        print(f"   Sample ID: {first_sample_id}")
        print(f"   Context: {context}")

    # Test 5: List workflows
    print("\n5. Listing workflows...")
    workflows = manager.list_workflows("test_user", "test_workspace")
    print(f"   Total workflows: {len(workflows)}")

    for workflow in workflows:
        print(f"\n   Workflow: {workflow.get('workflow_id')}")
        print(f"   Name: {workflow.get('name')}")
        print(f"   Nodes: {len(workflow.get('nodes', []))}")
        print(f"   Edges: {len(workflow.get('edges', []))}")

    # Test 6: Placeholder resolution simulation
    print("\n6. Simulating placeholder resolution...")
    if samples:
        sample_id = list(samples.keys())[0]
        context = manager.get_sample_context("test_user", "test_workspace", sample_id)

        # Test pattern
        pattern = "{sample}_proteoforms.tsv"
        print(f"   Pattern: {pattern}")
        print(f"   Context: {context}")

        try:
            resolved = pattern.format(**context)
            print(f"   Resolved: {resolved}")
        except KeyError as e:
            print(f"   ERROR: Missing key {e}")

    # Test 7: Directory structure verification
    print("\n7. Verifying directory structure...")
    dirs_to_check = [
        ("data/raw", "Raw data directory"),
        ("data/fasta", "FASTA database directory"),
        ("data/reference", "Reference data directory"),
        ("workflows", "Workflows directory"),
        ("executions", "Executions directory")
    ]

    for dir_path, description in dirs_to_check:
        full_path = workspace_path / dir_path
        exists = full_path.exists()
        file_count = len(list(full_path.iterdir())) if exists and full_path.is_dir() else 0
        status = "[OK]" if exists else "[MISSING]"
        print(f"   {status} {description}: {dir_path} ({file_count} files)")

    # Test 8: Data files verification
    print("\n8. Verifying test data files...")
    data_files = [
        ("data/raw/Sorghum-Histone0810162L20.raw", "Raw data"),
        ("data/fasta/UniProt_sorghum_focus1.fasta", "FASTA database")
    ]

    for file_path, description in data_files:
        full_path = workspace_path / file_path
        exists = full_path.exists()
        size_mb = full_path.stat().st_size / (1024*1024) if exists else 0
        status = "[OK]" if exists else "[MISSING]"
        print(f"   {status} {description}: {file_path} ({size_mb:.1f} MB)")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


def test_add_new_sample():
    """Test adding a new sample"""

    print("\n" + "=" * 60)
    print("Testing Add New Sample")
    print("=" * 60)

    manager = get_unified_workspace_manager("data")

    # Add a new sample
    print("\n1. Adding new sample...")
    sample_def = manager.add_sample(
        user_id="test_user",
        workspace_id="test_workspace",
        sample_id="sample2",
        name="Test Sample 2",
        description="Second test sample",
        context={
            "sample": "sample2",
            "fasta_filename": "UniProt_sorghum_focus1",
            "input_basename": "test_sample_2",
            "input_ext": "raw"
        },
        data_paths={
            "raw": "data/raw/test_sample_2.raw",
            "fasta": "data/fasta/UniProt_sorghum_focus1.fasta"
        },
        metadata={
            "organism": "Test organism",
            "tissue": "Test tissue"
        }
    )

    print(f"   Sample ID: {sample_def['id']}")
    print(f"   Name: {sample_def['name']}")
    print(f"   Context: {sample_def['context']}")

    # Verify sample was added
    print("\n2. Verifying sample was added...")
    samples = manager.list_samples("test_user", "test_workspace")
    print(f"   Total samples: {len(samples)}")

    for sample in samples:
        print(f"   - {sample['id']}: {sample['name']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_workspace_manager()
    # Uncomment to test adding samples:
    # test_add_new_sample()
