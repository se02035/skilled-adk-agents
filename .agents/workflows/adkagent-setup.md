---
description: Automates setting up a new Google ADK agent environment, configuring a Python virtual environment, scaffolding project files from examples, and verifying the test run.
---

# Workflow: Initialize ADK Project Environment

**Goal**: Create and initialize a new Google Agent Development Kit (ADK) project environment with a comprehensive, production-ready directory structure using `uv` for dependency management.

## Parameters
* `AGENT_SOLUTION_NAME`: Used as both the root project folder name and the target name for the agent solution under `src/agents/`.

---

## Steps

### 1. Install `uv`, Initialize Project, and Create Environment
Check if the `uv` package manager is installed. If not, install it. Then, initialize the project directory and create a new Python virtual environment.

```bash
# Install uv if not found
if ! command -v uv &> /dev/null; then
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    source $HOME/.cargo/env
fi

# Initialize the project directory (this automatically creates pyproject.toml and .gitignore)
uv init "{AGENT_SOLUTION_NAME}"
cd "{AGENT_SOLUTION_NAME}"

# Create and activate a new virtual environment
uv venv
source .venv/bin/activate
```

### 2. Install Google ADK
Use `uv` to fetch and add the latest Google ADK Python package with A2A (`google-adk[a2a]`) to your project dependencies.

```bash
# Add the Google ADK package to pyproject.toml and install it
uv add google-adk
```
*(Note: If the specific package name differs, e.g., `google-genai-adk`, update the package name here).*

### 3. Scaffold the Project Structure
The folder `.context/examples/` contains a sample implementation of an ADK A2A agent. Use that structure when creating a new ADK agent solution. Follow these rules:

- **Models**: Use the latest Gemini Flash Models (preview is OK).
- **Typings**: Usage of Typings is a must. Stick to `pydantic`.

The target folder for the new agent solution is under folder `src`.

### 4. Verify the Setup
Execute the newly created agent to confirm that the nested environment is configured correctly and runs without errors.

```bash
# Run the ADK agent from the new path
adk run "./src/agents/{AGENT_SOLUTION_NAME}/"
```