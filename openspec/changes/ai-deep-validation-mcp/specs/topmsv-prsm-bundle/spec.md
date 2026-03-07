## MODIFIED Requirements

### Requirement: PrSM Rendering
The TopMSV-PrSM-Bundle normally renders interactive tables of identified Proteoforms and their specific mass modifications.

#### Scenario: Rendering identified modifications
- **WHEN** the viewer initializes
- **THEN** it displays the PTM mass shifts (e.g., +79.96 Da) next to the sequence logo.

**MODIFIED Behavior:**
The PrSM viewer SHALL integrate the AI's external MCP knowledge as a foundational visual layer.

#### Scenario: Visualizing cross-validation scores
- **WHEN** the `ai-cross-validation` agent returns its Symmetrical Confidence Score
- **THEN** the PrSM viewer overlays a glowing "Validation Halo" on the modified residue in the sequence map, coloring it green for strong literature support or red for highly unlikely bio-chemical events, accompanied by a Copilot tooltip linking to the UniProt/PubMed reference.
