## 1. Tool definitions

- [x] 1.1 Update `config/tools/featuremap_viewer.json` so that the FeatureMap Viewer requires the upstream `.ms1feature`/`ms1ft` data input, documents the file in the description, and keeps the selection output port.
- [x] 1.2 Update `config/tools/spectrum_viewer.json` so that the Spectrum Viewer consumes the same `.ms1feature`/`ms1ft` dataset, keeps the `selection_in` state port, and renders the data as m/z vs intensity without assuming an `msalign` file.

## 2. Interactive workflows

- [x] 2.1 Rewrite `tests/test.json`, `data/users/test_user/workspaces/test_workspace/workflows/wf_test_full.json`, and `featuremap_demo.json` so that FeatureMap/Spectrum nodes read the `promex` MS1 feature output and the selection edge feeds into the Spectrum state port.

## 3. Verification

- [x] 3.1 Re-seed the workspace workflows (using `scripts/seed_workflow.py` or the batch command) and run the relevant integration/test command to confirm the workflow loads and the interactive nodes trigger off the MS1 feature file.

## 4. TopPIC alignment

- [x] 4.1 Extend `config/tools/toppic.json` with a `ms1feature` output and keep the viewers expecting the same `ms1feature` dataType so they display the `_ms1.feature` file coming from TopPIC.
- [x] 4.2 Adjust `data/users/test_user/workspaces/test_workspace/workflows/wf_test_full.json` to pipe the viewers from `toppic_1`'s `ms1feature` output, delete the extra workspace workflows (`featuremap_demo.json`, `test_pipeline.json`), and keep a single canonical workflow for seeding.
