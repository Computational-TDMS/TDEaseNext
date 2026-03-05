## MODIFIED Requirements

### Requirement: FeatureMap Viewer node
The system SHALL provide a FeatureMap Viewer node that displays mass spectrometry feature data as a scatter plot (RT vs Mass). It SHALL require an upstream `.ms1feature` dataset (mass, intensity, start_time, end_time) so that downstream interactive nodes can rely on consistent feature IDs and retention-time bounds.

#### Scenario: FeatureMap renders feature data
- **WHEN** the node receives tabular data with RT, Mass (or MassError), and Intensity columns
- **THEN** the system SHALL render a scatter plot with RT on the X axis, Mass on the Y axis
- **AND** point size or color SHALL encode Intensity
- **AND** the displayed data SHALL directly come from the upstream `.ms1feature` file rather than an arbitrary execution output.

#### Scenario: FeatureMap TopN rendering filter
- **WHEN** the user sets a TopN limit (e.g., 10000)
- **THEN** the system SHALL render only the top N features by Intensity
- **AND** the full dataset SHALL remain in memory (filter is display-only)

#### Scenario: FeatureMap brush selection
- **WHEN** the user draws a rectangular selection on the scatter plot
- **THEN** the system SHALL update the node's selection state with all features inside the bounding box
- **AND** downstream nodes connected to this node SHALL automatically update
- **AND** the node SHALL emit the selection state through its `selection` output port, including the MS1 feature identifiers and start_time/end_time limits.

#### Scenario: FeatureMap range filter
- **WHEN** the user sets RT range, Mass range, or Intensity range filters
- **THEN** the system SHALL update the selection state to reflect only features within those ranges

### Requirement: Spectrum Viewer node
The system SHALL provide a Spectrum Viewer node that displays mass spectrum data (m/z vs Intensity). It SHALL accept both the `.ms1feature` dataset and an interactive `selection_in` port so that Spectrum can render the selected MS1 feature peaks without duplication or further integration.

#### Scenario: Spectrum Viewer loads data from connected file
- **WHEN** the node's input is connected to a processing node's output port
- **THEN** the system SHALL load the connected file's data using the P1 node-data-access API
- **AND** render an m/z vs Intensity bar/line chart
- **AND** the connected file SHALL be the same `.ms1feature` dataset referenced by FeatureMap whenever the nodes are wired together.

#### Scenario: Spectrum Viewer filters by upstream selection
- **WHEN** the node's input is connected to an interactive node's selection state
- **THEN** the system SHALL display only the spectra/entries matching the upstream selection
- **AND** automatically re-render when the upstream selection changes
- **AND** the selection payload SHALL arrive via the `selection_in` port so that the data mappings remain consistent.

#### Scenario: Spectrum peak selection
- **WHEN** the user clicks or brush-selects peaks in the spectrum
- **THEN** the system SHALL update the node's selection state with selected peak indices

