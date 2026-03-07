## ADDED Requirements

### Requirement: Holographic Data Summarization
The `data-summarizer` node SHALL distill multi-gigabyte mass spectrometry data (TSVs, MZMLs) into highly dense, symbolic semantic signatures (Data Holograms) that represent the statistical fingerprint of the dataset.

#### Scenario: Summarizing raw spectrum data
- **WHEN** a TopFD or TopPIC node completes execution
- **THEN** the `data-summarizer` intercepts the output and computes a JSON Data Hologram containing dynamic SNR distributions, prominent peak cluster m/z, and hypothetical biological noise estimates, scaling down 500MB to a 50KB dense feature array.

### Requirement: Multimodal Shape Perception
The summarizer SHALL compute "shape descriptors" mapping the visual contour of the chromatogram and spectral envelopes into descriptive structural language.

#### Scenario: Visual contour mapping
- **WHEN** a spectral file is parsed
- **THEN** it appends text-based contour descriptors to the summary (e.g., "Gaussian elution with heavy tailing", "Bimodal N-terminal fragment distribution").
