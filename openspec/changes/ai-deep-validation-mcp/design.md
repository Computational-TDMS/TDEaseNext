## Context
Our analytical nodes (like TopPIC) are essentially mathematical engines. They predict mass shifts (Modifications) based purely on precursor mass minus theoretical fragmentation mass. However, they lack biological context—they might propose biologically impossible modifications. Scientists currently verify these inferences manually via UniProt and literature searches. We intend to empower high-capability Agent Models to act as "Literature Reviewers" via the Model Context Protocol (MCP), validating these algorithmic inferences autonomously.

## Goals / Non-Goals

**Goals:**
- Construct an MCP Server (`uniprot-mcp-server`) that strictly adheres to the widely adopted MCP standard, providing `fetch_protein_ptm` and `search_literature` tools.
- Implement an AI Cross-Validation workflow phase that runs globally across the `ExecStore` results, debating the mathematically inferred mass shifts against externally sourced biological ground truths.
- Seamlessly route between MCP/Tool-Calling for high-IQ models (e.g. Claude 3.5 Sonnet / GPT-4o) and simplified LangChain pre-fetched contexts for smaller local models (e.g. Llama-3 8B).

**Non-Goals:**
- Building a massive internal replica of UniProt. We fetch strictly on-demand via the external APIs.
- Auto-correcting or overwriting the raw mass-spec outputs. The AI acts as a reviewer overlay, not an editor.

## Decisions

- **MCP Protocol Adoption**: By deploying standard MCP, our server can be consumed not just by our internal TDEase agent, but by *any* standard AI client on the developer's laptop (e.g. Claude Desktop). This breaks our siloes and integrates TDEase into the broader Agent ecosystem.
- **Routing Engine**: We will implement a `ModelCapabilityRouter` in the LangGraph chain.
  - If `model.capabilities.includes('mcp_native')`: The LLM is given direct access to the MCP server.
  - Else: The backend Python script pre-fetches the UniProt record, crafts a dense Markdown summary, and feeds it into the LLM context window as a LangChain `system_message`.
- **Validation Halo UI**: The UI will not clutter the main interface with raw AI text. It will use a minimalist "Validation Halo" around the amino acid residue inside the TopMSV sequence viewer, reserving the detailed debate/literature links for a Copilot sidebar tooltip.

## Risks / Trade-offs

- **Risk: UniProt API rate limits.**
  - *Mitigation*: The MCP Server must implement LRU Caching for protein accessions to prevent duplicate external requests when an agent enters a self-correction loop or when analyzing multiplexed data.
- **Risk: AI hallucinations generating fake literature citations.**
  - *Mitigation*: The Agent's prompt will strictly enforce "Provide direct HTTPS links to PubMed DOIs. Do not summarize findings without a verifiable link."
