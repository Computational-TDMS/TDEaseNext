## Context
Visualizing top-down proteomics data involves rendering massive spectral graphs. Our AI models lack the capacity to visually perceive these plots or read a 500MB raw TSV. We need an architectural bridge to compress this dense biological data into semantic, text-friendly statistical features—what we call "Data Holograms"—so that an AI Agent can provide empathic and accurate diagnostic insights regarding data quality and structural fragmentation.

## Goals / Non-Goals

**Goals:**
- Implement a backend `Data Summarizer` pipeline hook that distills heavy spectral outputs (e.g., from TopFD) into a lightweight `<50KB` JSON summary (Data Hologram).
- Dynamically hook the frontend `topmsv-prsm-bundle` viewer into the `StateBus`, continually broadcasting micro-versions of this Data Hologram based on the user's active viewport (pan/zoom level).
- Create a conversational AI node that translates this Hologram into an "Empathic Diagnostic Report" for the user.

**Non-Goals:**
- Training our own multimodal foundation model. We will rely on text-based LLMs reasoning over our engineered data summaries, not visual image-to-text models processing screenshots.

## Decisions

- **The Data Hologram Schema**: We will define a strict JSON schema capturing key parameters:
  - `global_snr`: The holistic signal-to-noise ratio.
  - `peak_clusters`: An array of local m/z density neighborhoods.
  - `contour_shape`: An algorithmic interpretation of the peak envelope (e.g. Gaussian, bimodal, noisy tail).
- **Empathic Translation Protocol**: The AI prompt will be engineered with rigorous bioscience domain knowledge so it acts like a senior mass spectrometrist. It won't just say `SNR=12.5`, it will interpret: "With a high SNR of 12.5, your sample is highly purified, but the missing low-mass reporter ions suggest possible over-washing during extraction."
- **Viewport State Binding**: The `VisContainer` will fire debounced events indicating the current `[mz_start, mz_end]` window. The viewer's DataResolver will instantly aggregate stats for just those peaks and push it into the AI's short-term memory loop.

## Risks / Trade-offs

- **Risk: The summarizer logic filters out crucial unexpected biological phenomena (e.g., unknown modifications).** 
  - *Mitigation*: The Data Hologram will include a dedicated field for "Unassigned Variance"—quantifying the amount of high-intensity signal that cannot be explained by standard metrics, alerting the AI to mention "mysterious high-intensity artifacts" to the user.
- **Risk: Context overflow if the viewport is zoomed all the way out.**
  - *Mitigation*: Dynamic downsampling of the Hologram density based on the size of the viewport.
