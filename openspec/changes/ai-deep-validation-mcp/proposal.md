# Proposal: Deep Validation via MCP

## Why
After a workflow identifies probable PTMs (post-translational modifications) in the `topmsv` output, scientists spend hours cross-checking external databases (like UniProt or PubMed) to verify the biological plausibility of the results. By implementing an MCP (Model Context Protocol) tool suite, high-capability AI models can autonomously query these databases and validate the inferred modifications, falling back to a LangChain executor for lower-capability models.

## Capabilities
- `uniprot-mcp-server`: An MCP toolkit exposing UniProt modification queries so the AI can look up known PTMs for specific protein accessions.
- `ai-cross-validation`: An analytical feature that runs after workflow completion, comparing inferred mass shifts against externally sourced literature and database facts.

## Modified Capabilities
- `topmsv-prsm-bundle`: Will visualize the AI's cross-validation confidence scores alongside identified PRSMs.

## Impact
- Backend: Needs an MCP runtime or integration to bridge the AI engine with rapid UniProt REST API calls.
- AI Layer: Needs a routing mechanism to provide MCP access to capable models (e.g. Claude 3.5 Sonnet) or fallback to basic REST calls via LangChain for smaller models.
