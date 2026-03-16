# Examples

This directory contains sample implementations and templates for building agents using the Agent Development Kit (ADK).

## Folder Structure

```text
.context/examples/
├── README.md           # This file
└── agent_template/              # ADK Agent implementations (can contain multiple agents)
    ├── .env            # Environment variables for agent configuration
    ├── __init__.py     # Package initialization
    ├── a2a_agent.py    # A2A server implementation
    ├── agent.py        # Primary ADK Agent (root_agent) definition
    └── tools/          # Custom tools for the agent
        └── sample_weather_tool.py
```

## Sample ADK A2A Agent Implementation

This sample demonstrates how to create ADK agents and expose them as Agent-to-Agent (A2A) services. The `agent_template` folder is designed to host multiple agents, typically with one agent defined per Python file. In this template, the **`root_agent`** is located in `agent.py`.

### Components

- **`agent.py`**: This script defines the `root_agent`, which serves as the primary entry point. It initializes an ADK `Agent` object, loads configuration from the `.env` file, and registers tools. While this specific file contains the `root_agent`, the folder can easily be expanded with additional agent files.
- **`a2a_agent.py`**: This script takes the `root_agent` defined in `agent.py` and wraps it into an A2A-compliant web service using the `to_a2a` utility. It uses `uvicorn` to serve the application on a specified port.
- **`tools/sample_weather_tool.py`**: A simple example of a Python function that can be used as a tool by the agent. ADK automatically handles the conversion of function signatures to tool definitions that the LLM can understand.
- **`.env`**: Stores sensitive or configurable information such as the agent's name, model selection, and behavioral instructions.

### How it Works

1.  The agent's logic and tools are defined in `agent.py`.
2.  `a2a_agent.py` imports the agent and converts it into a FastAPI app (using `to_a2a`).
3.  When run, the agent becomes reachable via A2A protocols, allowing other agents or systems to interact with it through a standardized interface.
