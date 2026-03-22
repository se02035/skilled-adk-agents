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

## Prerequisites & Setup

1. **Python Virtual Environment**
First, setup a virtual environment and install the required dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. **Configure Environment Variables**
- Navigate to the `src/skill-agent/app` directory and locate/create the `.env` file.
- Update the `.env` file settings. Define whether the ADK native SkillToolset should be used or the custom MCP server (Skills Provider). Comment out any code you do not need.

1. **(Optional) Pre-Install Agent Skills**
Pre-install the necessary skill packages using the `skills` CLI toolkit. This is optional as the agent can install skills dynamically.
```bash
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```

1. **(Optional) Install Ngrok for Tunnels**
If you plan to expose the A2A server to external services (like Gemini Enterprise), install ngrok:
```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok

```

## How to ...

### Run using Google's ADK web tool
Running the ADK web tool provides a local web interface for interacting directly with the agent during development.

**Option 1: Using VS Code Debugger (Recommended)**
Open the Run and Debug view in VS Code and select the `adk web` configuration, then start debugging.

**Option 2: Using the Terminal**
From the `src/skill-agent` directory, run the ADK CLI directly:
```bash
python -m google.adk.cli web --no-reload --log_level debug
```

*(Note: If you run an MCP Skills Provider, ensure that is running either via the `mcp skills` run configuration or `npx @modelcontextprotocol/inspector` testing tool before launching the agent.)*

### Run using the A2A protocol
The A2A (Agent-to-Agent) protocol allows external agent frameworks and services to communicate securely with your agent.

**1. Start the A2A Server**
- **Option 1 (VS Code):** Run the `adk a2a` debug configuration.
- **Option 2 (Terminal):** From `src/skill-agent`, execute `python app/a2a_agent.py`.
This runs the lightweight REST/A2A server locally.

**2. Expose via Tunnel (Optional)**
Use ngrok to create a secure tunnel to your local A2A server (assuming it binds to port `8001`):
```bash
A2A_PORT=8001
npx ngrok http $A2A_PORT --host-header="localhost:$A2A_PORT"
```
After starting ngrok, take note of the public forwarding URL (e.g., `https://SOMETHING.ngrok-free.dev`) and update the `TUNNEL_ADDRESS` variable in your `.env` file.

### Connect with Gemini Enterprise
To integrate your agent with Gemini Enterprise using the A2A protocol:
1. Ensure the A2A server is running and exposed publicly via a secure tunnel like ngrok (see above).
2. Use the ngrok tunneling forwarding URL as the endpoint base URL to get the A2A agent card (using the URL like `<ngrok-url>/.well-known/agent.json`).
3. In Gemini Enterprise, register a new A2A Agent. When asked, provide the retrieved A2A agent card.
4. Open Gemini Enterprise's end-user web frontend and start interacting with the agent.