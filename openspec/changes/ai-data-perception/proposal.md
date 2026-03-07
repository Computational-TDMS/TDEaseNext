# Proposal: AI Data Perception & Feature Extraction

## Why
Raw mass spectrometry outputs (TSVs, chromatograms) can be extremely large, making them impossible for an AI context window to digest directly. By building specialized feature extraction nodes or embedding data perception directly into visualizer nodes, we can summarize the key properties (shape, peaks, SNRs, modifications) of the data into lightweight statistical summaries that an AI agent can interpret and diagnose.

## Capabilities
- `data-summarizer`: A backend extraction process (either as a node or integrated within the viewer's data resolver) that parses TopFD/TopPIC mass spectra outputs to extract concise statistical summaries.
- `ai-diagnostic-report`: An AI-based conversational evaluation that uses these summaries to tell the user the overall health and shape of the data.

## Modified Capabilities
- `topmsv-prsm-bundle`: The spectrum display bundle will now expose its parsed data features to the system for AI access.

## Impact
- Backend: DataResolverRegistry needs to support yielding summarized metadata alongside rendering subsets.
- Frontend: VisContainer needs a Copilot panel to display the AI's understanding of the active spectrum viewer.
