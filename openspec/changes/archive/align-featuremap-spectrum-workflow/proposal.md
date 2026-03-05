## Why

Current interactive workflows display feature map and spectrum viewers but still rely on generic node outputs instead of the MS1 feature files. The feature map is supposed to visualize .ms1feature data and hand the selection state to Spectrum, per docs/WORKFLOW_REQUIREMENTS.md. Fixing this flow removes the need for frontend mocks and keeps downstream investigation grounded in real MS1 data.

## What Changes

- Update the workflow definitions and the seeded wf_test_full to source data/users/.../workspaces/.../samples/ms1/ms1.feature (or other normalized MS1 feature files), drive FeatureMap selection, and stream selection state into the Spectrum node as described in the doc.
- Adjust config/tools/featuremap_viewer.json and config/tools/spectrum_viewer.json so their inputs explicitly accept the .ms1feature dataset (e.g., ms1feature_file) and the selection state ports needed to pass data between interactive nodes.
- Ensure scripts/seed_workflow.py (and any helpers used by data/users/.../workspaces/.../workflows) rewrites the workflow definition and persists it to the workspace, so IDE/DB views show the updated interactive flow without a separate frontend mock.
- Validate that tools reading workflow metadata and the backend selection propagation expect MS1 feature metadata instead of the previous generic file keys.

## Capabilities

### New Capabilities
- ms1-featuremap-spectrum-flow: Coordinate the FeatureMap and Spectrum interactive viewers to consume ms1.feature data, carry brush/click selection state from FeatureMap into Spectrum, and satisfy the MS1-focused exploration requirements from the workflow document.

### Modified Capabilities
- interactive-visualization-nodes: Update the requirement to guarantee FeatureMap/Spectrum input ports align with MS1 feature data and that selection states share consistent labels (e.g., selection, selection_in) so downstream nodes can trust the interactive contract.

## Impact

- Touches config/tools/featuremap_viewer.json, config/tools/spectrum_viewer.json, and any backend mapping that interprets tool inputs/outputs for interactive state propagation.
- Overwrites the workspace workflow JSON under data/users/test_user/workspaces/test_workspace and reruns scripts/seed_workflow.py (or equivalent) so the DB and storage reflect the new interactive flow.
- Requires spec updates and documentation so future workflows understand how FeatureMap selection maps directly into Spectrum and how to label MS1 feature data sources.
