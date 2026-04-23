# Skilled ADK Agents

> [!WARNING]
> **DISCLAIMER**: The implementation in this repository is **not** meant for production use. It is intended solely for development, testing, and demonstration purposes.

## Overview / Introduction
This repository demonstrates how to build and operate advanced artificial intelligence agents using Google's Agent Development Kit (ADK). The project provides examples of agents equipped with extensible "skills" (via MCP servers or native toolsets) capable of performing complex actions. It showcases how developers can test agents locally through the ADK web tool or expose them over the Agent-to-Agent (A2A) protocol to connect seamlessly with broader platforms like Gemini Enterprise.

> [!WARNING]
> Please be aware that this solution may execute shell commands on your local machine to fulfill certain agent capabilities (like installing skills). This can lead to unwanted or unforeseen behavior. Proceed with caution and ensure you understand the actions the agent is instructed to perform.

### Repository Structure & Architecture
The project logic is organized into several key directories:
- **`.agents/` folder**: This directory stores agent-specific configurations and modular tools. Notably, the `.agents/skills` subdirectory houses the executable tools, such as the `find-skills` capability, allowing the agent to dynamically discover and install new functionalities.
- **`src/` folder**: This contains the core application logic, split into two main components:
  - `src/skill-agent`: The primary directory for the ADK agent's logic and the A2A server endpoint setup. The agent acts as the decision engine that queries tools and processes responses.
  - `src/mcp-skills-provider`: A standalone Model Context Protocol (MCP) server that acts as a unified provider for the skills located in the `.agents/skills` directory. The main ADK agent connects to this MCP server over HTTP/STDIO to utilize these external tools safely and consistently.

### Conceptual High-Level Architecture
```mermaid
flowchart LR
    U[Developer / User]
    ADKWeb[ADK Web UI]
    A2AClient[External A2A Client - Gemini Enterprise]

    subgraph AgentRuntime[Skill Agent Runtime]
        SA[ADK Agent src/skill-agent]
        ENV[Config src/skill-agent/app/.env]
    end

    subgraph MCPServers[MCP Servers Used by Agent]
        SkillsMCP[Skills MCP Server src/mcp-skills-provider]
        ShellMCP[Shell MCP Server mcp-shell-server shell_execute]
    end

    subgraph Dependencies[Required Dependencies]
        FS[Local filesystem / disk]
        Compute[Local compute sandbox current implementation your machine]
        SkillsRepo[skills.sh catalog used by find-skills]
        SKILLS[.agents/skills installed skills SKILL.md and scripts]
    end

    subgraph Cloud[Google Cloud / Vertex AI]
        MODEL[Gemini Model]
    end

    U --> ADKWeb
    ADKWeb --> SA
    A2AClient -->|HTTP / A2A| SA
    ENV -. config .-> SA
    SA -->|MCP over HTTP| SkillsMCP
    SA -->|MCP over stdio| ShellMCP
    SkillsMCP -->|list/read local skills| SKILLS
    SkillsMCP -->|requires access| FS
    ShellMCP -->|executes allowed commands on| Compute
    SKILLS -. discover new skills .-> SkillsRepo
    SA -->|LLM calls| MODEL

    classDef entry fill:#eef2ff,stroke:#4f46e5,stroke-width:1px,color:#111827;
    classDef runtime fill:#e0f2fe,stroke:#0284c7,stroke-width:1px,color:#111827;
    classDef mcp fill:#ede9fe,stroke:#7c3aed,stroke-width:1px,color:#111827;
    classDef deps fill:#fff7ed,stroke:#ea580c,stroke-width:1px,color:#111827;
    classDef cloud fill:#dcfce7,stroke:#16a34a,stroke-width:1px,color:#111827;

    class U,ADKWeb,A2AClient entry;
    class SA,ENV runtime;
    class SkillsMCP,ShellMCP mcp;
    class FS,Compute,SkillsRepo,SKILLS deps;
    class MODEL cloud;
```

Flow summary: users interact through ADK web or A2A, the ADK agent calls two MCP servers (Skills + Shell), and those servers depend on local resources (filesystem and compute). New skills discovered by `find-skills` come from [skills.sh](https://skills.sh/).

## Prerequisites & Setup

**Requirements**
- **Python 3.12+** (see `pyproject.toml` / `requires-python`)
- **Git** to clone the repository
- **Node.js and npm** (only if you use the optional `npx` steps below, e.g. the skills CLI or `npx ngrok`)

### 1. Create a virtual environment and install dependencies

From the **repository root**:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

This installs the ADK app stack (`google-adk`, MCP, etc.); see `requirements.txt` for the exact pins.

### 2. (Optional) Development tooling and git hooks

If you are contributing or want local linting and pre-commit (ruff, pyright — see `pyproject.toml` and `.pre-commit-config.yaml`):

```bash
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

You can also run linters directly:

```bash
ruff check src
ruff format src
pyright
```

### 3. Environment variables

1. Copy the example env file to an active `.env` used by the agent:

   ```bash
   cp src/skill-agent/app/.env.example src/skill-agent/app/.env
   ```

2. Edit `src/skill-agent/app/.env` and set at least the Google Cloud / Vertex and agent settings (see the comments in `.env.example`). If you use the **in-repo MCP Skills Provider** (HTTP on port `5555` by default), keep `MCP_SKILLS_PROVIDER_ENDPOINT` in sync, or point it to your own MCP server.

`config` loads this file from `app/.env` automatically (you do not need a duplicate `.env` in the repo root for normal runs from `src/skill-agent`).

### 4. (Optional) Pre-install agent skills

Pre-install skills with the Vercel `skills` CLI. **Optional** — the agent can also discover and install skills at runtime. Requires Node/npm for `npx`:

The `find-skills` workflow searches the public skills catalog at [skills.sh](https://skills.sh/).

```bash
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```

### 5. (Optional) ngrok for public tunnels (e.g. Gemini Enterprise)

The examples below use `A2A_PORT=8001` and call ngrok; you can use a **globally installed** binary or `npx` (if you prefer not to install ngrok with your OS package manager).

- **macOS (Homebrew):** `brew install ngrok/ngrok/ngrok`
- **Debian / Ubuntu (apt):** see [ngrok’s Linux install guide](https://ngrok.com/docs/getting-started)
- **Any OS:** [download the binary](https://ngrok.com/download) or use `npx ngrok` as shown in the A2A section

## How to …

With your virtual environment **activated** (`source .venv/bin/activate` from the repo root), all commands below assume you are in the stated working directory.

### Start the MCP Skills Provider (when using the HTTP skills server)

If your `.env` points `MCP_SKILLS_PROVIDER_ENDPOINT` at the bundled provider (default `http://0.0.0.0:5555/mcp`), start the server **before** the ADK app.

**VS Code:** use the `mcp skills` launch configuration (see `.vscode/launch.json` — it sets `SKILLS_DIRECTORY` to the repo’s `.agents/skills` and `PORT=5555`).

**Terminal** (`server.py` defaults to the repository’s `.agents/skills` directory and port `5555` unless you set `SKILLS_DIRECTORY` or `PORT`):

```bash
cd src/mcp-skills-provider
python server.py
```

You can also use the MCP inspector or other clients; the critical part is that the URL in `.env` matches a running process.

### Run using Google’s ADK web tool
The ADK web UI is for day-to-day development and chat against the agent.

**Option 1: VS Code / Cursor (recommended)**  
Run and Debug → choose `adk web` (uses `src/skill-agent/app/.env` via `envFile` in `.vscode/launch.json`).

**Option 2: Terminal**  
With the venv active:

```bash
cd src/skill-agent
python -m google.adk.cli web --no-reload --log_level debug
```

If you rely on the MCP provider, start it (section above) first.

### Run using the A2A protocol
A2A lets other frameworks call your agent over HTTP.

**1. Start the A2A server**
- **VS Code / Cursor:** `adk a2a` in `.vscode/launch.json` (loads `app/.env`).
- **Terminal** (with venv active):

  ```bash
  cd src/skill-agent
  python app/a2a_agent.py
  ```

  Default port comes from `A2A_PORT` in `app/.env` (see `.env.example`, typically `8001`).

**2. Expose via tunnel (optional)**  
Use the same `A2A_PORT` as in `app/.env` (example below uses `8001`). If you use the MCP skills provider, start it before the agent, as in the web UI section.

```bash
A2A_PORT=8001
npx ngrok http $A2A_PORT --host-header="localhost:$A2A_PORT"
```

Copy the HTTPS forwarding URL (e.g. `https://SOMETHING.ngrok-free.dev`) into `TUNNEL_ADDRESS` in `src/skill-agent/app/.env`.

### Connect with Gemini Enterprise
To integrate your agent with Gemini Enterprise using the A2A protocol:
1. Ensure the A2A server is running and exposed publicly via a secure tunnel like ngrok (see above).
2. Use the ngrok tunneling forwarding URL as the endpoint base URL to get the A2A agent card (using the URL like `<ngrok-url>/.well-known/agent.json`).
3. In Gemini Enterprise, register a new A2A Agent. When asked, provide the retrieved A2A agent card.
4. Open Gemini Enterprise's end-user web frontend and start interacting with the agent.