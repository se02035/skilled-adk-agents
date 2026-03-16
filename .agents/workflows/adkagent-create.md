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
Create the target directory for the new agent solution under `src/agents/` and copy the A2A enabled template files.

```bash
# Create the target directory structure
mkdir -p "src/agents/{AGENT_SOLUTION_NAME}"

# Copy the template files from .context/examples/agent_template
cp -r .context/examples/agent_template/* "src/agents/{AGENT_SOLUTION_NAME}/"

# Customize the agent configuration in .env and pyproject.toml
# Replace placeholders with actual values (e.g., using sed or manually)
# Placeholders: {AGENT_NAME}, {AGENT_VERSION}, {AGENT_DESCRIPTION}, {AGENT_INSTRUCTION}, {TARGET_PORT}
```

Follow these rules for customization:
- **Models**: Use the latest Gemini Flash Models (e.g., `gemini-2.5-flash`).
- **Typings**: Usage of Typings is a must. Use `pydantic` for structured data.
- **A2A Support**: The template includes `a2a_agent.py` to expose the agent via the A2A protocol.

### 4. Verify the Setup
Confirm the agent is configured correctly by running it in development mode or starting the A2A server.

**Option A: ADK CLI (Development)**
```bash
# Run the ADK agent logic
adk run "./src/agents/{AGENT_SOLUTION_NAME}/app/"
```

**Option B: A2A Server**
```bash
# Start the A2A enabled server
export PYTHONPATH=$PYTHONPATH:$(pwd)/src/agents/{AGENT_SOLUTION_NAME}/app
python "src/agents/{AGENT_SOLUTION_NAME}/app/a2a_agent.py"
```