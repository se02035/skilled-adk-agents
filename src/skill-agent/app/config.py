import os
from dotenv import load_dotenv
import requests

load_dotenv()

def get_http_content(url: str) -> str:
    """
    Fetches the markdown content from the given URL.
    """
    try:
        response = requests.get(url)
        # Check if the request was successful
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching the content: {e}"

agent_skills_specification = get_http_content("https://agentskills.io/specification.md")


ADK_AGENT_INSTRUCTION = """
#AGENT INSTRUCTIONS:
You are a highly capable AI assistant equipped with an extensible skill system. Your objective is to fulfill user requests by effectively leveraging these specialized tools.

**CORE OPERATING PROCEDURE:**
You must adhere strictly to the following step-by-step workflow for every user request:

1. **Discover:** Always begin by calling the `list_skills` tool to retrieve the current catalog of available skills.
2. **Assess & Inspect:** Evaluate the returned list and select the most relevant skill for the user's task. Before attempting to use the selected skill, you must call the `read_skill` tool to review its exact instructions and requirements.
3. **Fallback (Missing Skills):** If no suitable skill is found in step 1:
    - Politely inform the user that you are searching for an appropriate skill to handle their request.
    - Call the `read_skill` tool specifically for the `find-skills` tool to understand its usage.
    - Execute the `find-skills` tool to locate a new capability that matches the request.
4. **Execute:** Carry out the task strictly based on the documentation retrieved in step 2 or 3. If a skill's documentation instructs you to execute shell commands, you must use the `shell_runner` tool to run them.

# AGENT SKILLS SPECIFICATION:
The complete agent skills specification can be found under: https://agentskills.io/llms.txt
Look up the specification to get more details around Skill resources like where to find skills scripts, assets, etc.
"""

ADK_AGENT_NAME = os.getenv('ADK_AGENT_NAME', 'skill-assistant') 
ADK_AGENT_MODEL = os.getenv('ADK_AGENT_MODEL', 'gemini-2.5-flash')
ADK_AGENT_DESCRIPTION = os.getenv('ADK_AGENT_DESCRIPTION', 'A skills-based assistant.')
SKILLS_DIRECTORY = os.getenv("SKILLS_DIRECTORY", "")

SHELL_RUNNER_ALLOWED_COMMANDS = os.getenv("MCP_SHELL_RUNNER_ALLOWED_COMMANDS","")
SHELL_RUNNER_ALLOWED_PATTERNS = os.getenv("MCP_SHELL_RUNNER_ALLOWED_PATTERNS","")

MCP_SERVER_URL_SKILLS_PROVIDER = os.getenv("MCP_SKILLS_PROVIDER_ENDPOINT")

WORKSPACE_DIRECTORY = os.getenv("MCP_SKILLS_PROVIDER_WORKSPACE_DIRECTORY")