## ADDED Requirements

### Requirement: FeatureMap loads MS1 feature tables
The system SHALL require the FeatureMap interactive node to read a `.ms1feature` dataset (mass, intensity, start_time, end_time) produced by upstream feature detection, and it SHALL expose that data for visualization with RT on the X axis and mass on the Y axis as documented in docs/WORKFLOW_REQUIREMENTS.md.

#### Scenario: FeatureMap renders MS1 feature data
- **WHEN** the FeatureMap node is connected or pointed to a file whose metadata declares `dataType: "ms1feature"` or whose filename ends with `.ms1feature`
- **THEN** the backend SHALL stream the retention-time, mass, and intensity tuples from that file to the viewer and render them as a scatter plot with RT on X, mass on Y, and color/size encoding intensity.

#### Scenario: FeatureMap selection represents MS1 feature IDs
- **WHEN** a user draws a brush selection on the scatter plot
- **THEN** the node SHALL emit a selection state that includes the MS1 feature IDs (or the feature coordinates) along with start_time/end_time bounds and pass that state through its `selection` output port.

### Requirement: Spectrum consumes FeatureMap selections
The Spectrum interactive node SHALL accept both an `ms1feature_file` input and a `selection_in` state so it can render only the selected features as m/z vs intensity peaks without extra integration.

#### Scenario: Spectrum filters peaks by FeatureMap selection
- **WHEN** the Spectrum node receives a selection payload on `selection_in` while the connected processing node supplies the same `.ms1feature` file
- **THEN** it SHALL reload the subset of peaks described by the selection, map each selected feature's mass to the X axis (m/z) and intensity to the Y axis, and render the filtered spectrum with the expected axis labels.

#### Scenario: Spectrum handles direct MS1 file loads
- **WHEN** a Spectrum node is instantiated with an `ms1feature_file` but no upstream selection
- **THEN** it SHALL still render the full set of peaks described in that file so analysts can inspect the entire MS1 data before selecting downstream features.
