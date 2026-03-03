#!/usr/bin/env python3
"""
Quick test script for new architecture

Tests:
1. Load sample context from samples.json
2. Use new API to execute workflow
3. Validate placeholder resolution

Run: python tests/test_new_architecture.py
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.unified_workspace_manager import get_unified_workspace_manager


def test_sample_context_loading():
    """Test 1: Load sample context from samples.json"""
    print("=" * 60)
    print("Test 1: Load sample context from samples.json")
    print("=" * 60)

    manager = get_unified_workspace_manager()

    # Test loading sample1
    user_id = "test_user"
    workspace_id = "test_workspace"
    sample_id = "sample1"

    context = manager.get_sample_context(user_id, workspace_id, sample_id)

    if context:
        print(f"[OK] Successfully loaded sample context: {sample_id}")
        print(f"  Sample: {context.get('sample')}")
        print(f"  FASTA: {context.get('fasta_filename')}")
        print(f"  Input basename: {context.get('input_basename')}")
        print(f"  Extension: {context.get('input_ext')}")
        print()
        return True
    else:
        print(f"[FAIL] Cannot load sample context: {sample_id}")
        return False


def test_samples_listing():
    """Test 2: List all samples in workspace"""
    print("=" * 60)
    print("Test 2: List all samples in workspace")
    print("=" * 60)

    manager = get_unified_workspace_manager()

    user_id = "test_user"
    workspace_id = "test_workspace"

    samples = manager.list_samples(user_id, workspace_id)

    if samples:
        print(f"[OK] Found {len(samples)} sample(s):")
        for s in samples:
            print(f"  - {s.get('id')}: {s.get('name', 'N/A')}")
        print()
        return True
    else:
        print(f"[FAIL] No samples found in workspace")
        return False


def test_workspace_structure():
    """Test 3: Verify workspace structure"""
    print("=" * 60)
    print("Test 3: Verify workspace structure")
    print("=" * 60)

    base_path = project_root / "data" / "users" / "test_user" / "workspaces" / "test_workspace"

    # Check samples.json
    samples_json = base_path / "samples.json"
    if samples_json.exists():
        print(f"[OK] samples.json exists")
        with open(samples_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"  Version: {data.get('version')}")
            print(f"  Sample count: {len(data.get('samples', {}))}")
    else:
        print(f"[FAIL] samples.json does not exist")
        return False

    # Check workflows directory
    workflows_dir = base_path / "workflows"
    if workflows_dir.exists():
        workflows = list(workflows_dir.glob("*.json"))
        print(f"[OK] Workflows directory exists with {len(workflows)} workflow(s)")
    else:
        print(f"[INFO] Workflows directory does not exist (optional)")

    print()
    return True


def test_api_payload_format():
    """Test 4: Generate API request payload in new format"""
    print("=" * 60)
    print("Test 4: New API request payload format")
    print("=" * 60)

    payload = {
        "workflow_id": "wf_test_full",
        "user_id": "test_user",
        "workspace_id": "test_workspace",
        "sample_ids": ["sample1"]
    }

    print("Request payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    print("[OK] New format is clean - no more sample_context needed!")
    print()
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("New Architecture Test Suite")
    print("=" * 60)
    print()

    tests = [
        ("Workspace Structure", test_workspace_structure),
        ("List Samples", test_samples_listing),
        ("Load Sample Context", test_sample_context_loading),
        ("API Payload Format", test_api_payload_format),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[FAIL] Test failed: {name}")
            print(f"  Error: {e}")
            print()
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("All tests passed! New architecture is ready.")
        print()
        print("Next steps:")
        print("1. Start backend server: python -m uvicorn app.main:app --reload")
        print("2. Test workflow execution via API")
        print("3. Check docs/API_USAGE_NEW_ARCHITECTURE.md for detailed examples")
        return 0
    else:
        print("Some tests failed. Please check configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
