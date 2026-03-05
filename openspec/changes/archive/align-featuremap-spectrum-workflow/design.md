## Context
The interactive workflows currently visualize FeatureMap and Spectrum nodes using generic execution outputs. According to docs/WORKFLOW_REQUIREMENTS.md, both viewers should be rooted in the `.ms1feature` data produced by the backend and exchange selection states so that users can explore the MS1 distribution before moving on to downstream tools.

## Goals / Non-Goals

**Goals:**
- Align the FeatureMap and Spectrum viewers with the true `.ms1feature` datasets so the UI no longer depends on mocked state.
- Introduce explicit `ms1feature_file`, `selection`, and `selection_in` ports so that selection state flows from FeatureMap into Spectrum while remaining compatible with the existing node-state APIs.
- Seed the updated workflow definition into data/users/test_user/workspaces/test_workspace and the database so IDE/workspace views show the new interactive branch.

**Non-Goals:**
- Implement MS2 PrSM parsing or Table interactions described later in the requirements document.
- Rewrite the entire execution engine or frontend components unrelated to FeatureMap/Spectrum data ports.

## Decisions
1. **Canonical data source:** Always load `.ms1feature` files for both FeatureMap and Spectrum nodes, because the requirements document calls out RT/mass/intensity axes and ensures selection state matches known feature IDs.
2. **State plumbing:** Use the `selection` output port on FeatureMap and the `selection_in` input on Spectrum so downstream viewers can subscribe to selection changes without tight coupling. This matches the docs flow (FeatureMap -> Spectrum) and keeps selection metadata in the backend.
3. **Workflow seeding:** Re-run `uv run python scripts/seed_workflow.py --workflow-dir data/users/test_user/workspaces/test_workspace/workflows --glob *.json` (or a similar command) to persist the interactive branch into the DB and workspace directory, avoiding separate frontend mocks.

## Risks / Trade-offs
- [Risk] Some legacy workflows or tooling may still expect the old field names, causing regressions. -> Mitigation: Update config/tools JSON definitions in tandem and keep the previous ports until all references are updated.
- [Risk] The `.ms1feature` files reside in different subdirectories for other samples, so hardcoding a single path may fail. -> Mitigation: Keep the workflow reference relative to the workspace’s samples directory and/or allow the seed script to rewrite the path per workspace.

## Migration Plan
1. Update config/tools/*.json to include `ms1feature_file` inputs and the new selection ports.
2. Overwrite data/users/test_user/workspaces/test_workspace/workflows/wf_test_full.json (and any referenced workflow JSONs) to point to the `.ms1feature` dataset and to insert the FeatureMap -> Spectrum edge with `selection_in` state.
3. Run `uv run python scripts/seed_workflow.py --workflow-dir data/users/test_user/workspaces/test_workspace/workflows --glob *.json` (or equivalent command) to persist the change into the DB and propagate to the UI.
4. Execute targeted tests or integration checks (e.g., tests/test_workflow_execution.py) to verify that interactive nodes load ms1feature data and that selection state is delivered.

## Open Questions
- Should `selection_in` carry the full MS1 feature payload or just IDs, given the FeatureMap already knows the masses? Clarifying this will guide the backend serialization format.
- Are there other interactive nodes (e.g., TableViewer) that need new state ports once FeatureMap/Spectrum dependencies change?
