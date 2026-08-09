# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **Skilled ADK Agents** project: a Python 3.12 product made of two local
services plus a required LLM backend. There is **no database, no build step, and no automated
test suite** (CI only runs lint). Standard setup/run commands live in `README.md`,
`scripts/ci-lint.sh`, and `.vscode/launch.json` — prefer those; the notes below only capture
non-obvious caveats discovered while setting up the cloud environment.

### Services
- `src/mcp-skills-provider` — FastMCP HTTP server (port `5555`) exposing `list_skills` /
  `read_skill` over `/mcp`. Run: `cd src/mcp-skills-provider && python server.py`.
- `src/skill-agent` — the ADK agent. Two entrypoints (run from `src/skill-agent`):
  - ADK Web UI: `python -m google.adk.cli web --no-reload --port 8080` (agent shows up as `app`).
  - A2A server: `python app/a2a_agent.py` (port `8001`; agent card at
    `/.well-known/agent-card.json`).

### Non-obvious caveats
- **Always activate the venv (`source .venv/bin/activate`) before running the agent.** The agent
  spawns the shell-runner MCP via `uvx mcp-shell-server` as a subprocess, so `uvx` must be on
  `PATH`. `uv` is installed *into the venv*, so running the interpreter directly
  (e.g. `.venv/bin/python app/a2a_agent.py`) without activation fails with
  `No such file or directory: 'uvx'` during tool/agent-card loading.
- **Start the MCP Skills Provider (port 5555) before the agent.** `agent.py` connects to
  `MCP_SKILLS_PROVIDER_ENDPOINT` while loading tools / building the A2A agent card.
- **Config lives at `src/skill-agent/app/.env`** (copy from `app/.env.example`; it is gitignored).
- **An LLM backend is required for the agent to actually respond.** Use Gemini/Vertex
  (`GOOGLE_CLOUD_PROJECT` + ADC, or a Gemini API key) **or** a LiteLLM proxy
  (`ADK_AGENT_MODEL=litellm`, `LITELLM_API_BASE`, `LITELLM_MODEL`, `LITELLM_VIRTUAL_KEY`).
  Listing/reading skills via the MCP provider works without any LLM, but chat does not.
- **Fully-local LLM option (no cloud creds):** run Ollama + a LiteLLM proxy. In this VM the
  default current Ollama build segfaults (`llama-server ... segmentation fault`); install a
  pinned older build instead (`OLLAMA_VERSION=0.6.8` worked). Run the LiteLLM proxy from a
  **separate** venv — `litellm[proxy]` downgrades `uvicorn`/`mcp` and conflicts with the project
  venv if installed there.
- **Lint** (the only CI gate) is run via `pre-commit run --all-files` (ruff, ruff-format,
  pyright); `scripts/ci-lint.sh` mirrors CI. Requires `requirements-dev.txt` installed.
