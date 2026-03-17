"""
Filename: agent.py
Author: Oliver Lintner  
Date: 2026-02-22
Version: 1.0
Description: 
    This script demonstrates a sample ADK agent (called 'root_agent'). 
    It demonstrates how to create an ADK agent with a tool.
    The agent uses a .env file to load its configuration (e.g. model, tools, etc.)

Validation:
    Run the `root_agent` using Google ADKs `adk run` command starting a conversation with 'Hi'. 
    The agent must successfully respond with a greeting.

License: MIT License
Contact: [EMAIL_ADDRESS]
Dependencies: google.adk.agents, tools.sample_weather_tool, .env
"""
import logging
import os
import pathlib
import yaml
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.skills import models
from google.adk.tools import skill_toolset
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

load_dotenv()

def load_skill_from_dir(skill_path: pathlib.Path) -> models.Skill:
    """Manually load a skill from a directory."""
    skill_md_path = skill_path / "SKILL.md"
    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}")
        
    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split frontmatter and body
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid SKILL.md format in {skill_path} - missing frontmatter delimiters")
    
    frontmatter_dict = yaml.safe_load(parts[1])
    instructions = parts[2].strip()
    
    metadata_raw = frontmatter_dict.get("metadata", {})
    sanitized_metadata = {}
    if isinstance(metadata_raw, dict):
        for k, v in metadata_raw.items():
            if isinstance(v, (dict, list)):
                import json
                sanitized_metadata[k] = json.dumps(v)
            else:
                sanitized_metadata[k] = str(v)
    frontmatter_dict["metadata"] = sanitized_metadata
    
    frontmatter = models.Frontmatter(**frontmatter_dict)

    
    resources = models.Resources()
    
    # Load references
    refs_dir = skill_path / "references"
    if refs_dir.exists():
        for ref_file in refs_dir.glob("*.md"):
            with open(ref_file, "r", encoding="utf-8") as f:
                resources.references[ref_file.name] = f.read()
                
    # Load assets
    assets_dir = skill_path / "assets"
    if assets_dir.exists():
        for asset_file in assets_dir.iterdir():
            if asset_file.is_file():
                try:
                    with open(asset_file, "r", encoding="utf-8") as f:
                        resources.assets[asset_file.name] = f.read()
                except Exception:
                    # Skip binary files if any
                    continue
                    
    return models.Skill(
        frontmatter=frontmatter,
        instructions=instructions,
        resources=resources
    )

ADK_AGENT_NAME = os.getenv('ADK_AGENT_NAME', 'skill-assistant')
ADK_AGENT_MODEL = os.getenv('ADK_AGENT_MODEL', 'gemini-2.0-flash')
ADK_AGENT_INSTRUCTION = os.getenv('ADK_AGENT_INSTRUCTION', 'You are a helpful assistant.')
ADK_AGENT_DESCRIPTION = os.getenv('ADK_AGENT_DESCRIPTION', 'A skills-based assistant.')

logger.info(f"--- 🤖 Creating ADK Agent: {ADK_AGENT_NAME} ---")

# root is 4 levels up
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent.parent
SKILLS_DIR = ROOT_DIR / ".agents" / "skills"

def load_tools() -> List:
    loaded_skills = []
    if SKILLS_DIR.exists():
        for skill_path in SKILLS_DIR.iterdir():
            if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                try:
                    skill = load_skill_from_dir(skill_path)
                    loaded_skills.append(skill)
                    logger.info(f"Successfully loaded skill: {skill_path.name}")
                except Exception as e:
                    logger.error(f"Failed to load skill {skill_path.name}: {e}")
    else:
        logger.warning(f"Skills directory not found at: {SKILLS_DIR}")

    # tools logic
    tools = []
    if loaded_skills:
        tools.append(skill_toolset.SkillToolset(skills=loaded_skills))

    shell_runner = McpToolset(
                connection_params=StdioConnectionParams(
                    server_params = StdioServerParameters(
                        command='uv',
                        args=[
                            "--directory",
                            "/Users/oliverli/Dev/demo-speckit-skills/asp/.agents/",
                            "run",
                            "mcp-shell-server"
                        ],
                        env= {
                            "ALLOW_COMMANDS": "gws,npx"
                        }
                    ),
                ),
                # Optional: Filter which tools from the MCP server are exposed
            )
    tools.append(shell_runner)
    return tools

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    # Get full tool list from MCP or agent.tools
    #all_tools = callback_context.agent.tools

    # # Use RAG to filter relevant tools based on user query or context
    # user_query = ctx.messages[-1].content if ctx.messages else ""
    # filtered_tools = rag_filter_tools(user_query, all_tools)

    # Temporarily override tools for this invocation
    callback_context.tools = load_tools()


root_agent = Agent(
    name=ADK_AGENT_NAME,
    model=ADK_AGENT_MODEL,
    description=ADK_AGENT_DESCRIPTION,
    instruction=ADK_AGENT_INSTRUCTION,
    tools=load_tools(),
    before_agent_callback=before_agent_callback
)

from google.adk.apps import App

app = App(root_agent=root_agent, name="app")


