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

from google.adk.agents import Agent
from google.adk.skills import models
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from google.adk.code_executors.unsafe_local_code_executor import UnsafeLocalCodeExecutor
from google.adk.tools.skill_toolset import SkillToolset
from google.adk.skills import load_skill_from_dir

from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, StreamableHTTPConnectionParams
from mcp import StdioServerParameters

from typing import Optional, Dict, Any

from . import config

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

logger.info(config.ADK_AGENT_INSTRUCTION)


def load_skills(skills_parent_path: pathlib.Path) -> list[models.Skill]:
    """
    Manually load a skill from a directory.

    Args:
        skill_path (pathlib.Path): The path to the skill directory.

    Returns:
        a list of models.Skill: The loaded skills. one found directory per 
    """
    loaded_skills = []
    
    # Iterate through the parent directory
    for skill_path in skills_parent_path.iterdir():
        # Check if the item is a folder
        if skill_path.is_dir():
            # Get the full absolute path as a string
            full_path = str(skill_path.resolve())
            
            # Load the Skill object and append it to our list
            skill = load_skill_from_dir(full_path)
            loaded_skills.append(skill)

            logger.info(f"Successfully loaded skill: {full_path}")
    
    return loaded_skills

def load_tools() -> list:
    """
    collect agent tools
    """
    tools = []

    # ==============================
    # OPTION #1
    # USE THE ADK SKILLS FEATURE (RELOAD OF SKILLS IS NOT SUPPORTED CURENTLY)
    # ==============================
    # loaded_skills = load_skills(pathlib.Path(config.SKILLS_DIRECTORY))

    # if loaded_skills:
    #     tools.append(
    #         SkillToolset(
    #             skills=loaded_skills,
    #             code_executor=UnsafeLocalCodeExecutor())
    #             )

    # ==============================
    # OPTION #2
    # USE AN MCP SERVER TO PROVIDE SKILLS
    # ==============================

    skills_provider = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=config.MCP_SERVER_URL_SKILLS_PROVIDER,
            timeout=180
        ),
    )
    tools.append(skills_provider)

    shell_runner = MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params = StdioServerParameters(
                        command='uv',
                        args=[
                            "run",
                            "mcp-shell-server",
                        ],
                        env= {
                            "ALLOW_COMMANDS": config.SHELL_RUNNER_ALLOWED_COMMANDS,
                            "ALLOW_PATTERNS": config.SHELL_RUNNER_ALLOWED_PATTERNS,
                        }
                    ),
                    timeout=180
                ),
                # Optional: Filter which tools from the MCP server are exposed
            )
    tools.append(shell_runner)

    return tools

def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    agent_name = tool_context.agent_name
    tool_name = tool.name

    # there seems to be a glitch in the implementation around the directory parameter.
    # we want to ensure that the execution directory is set to the workspace directory.
    if tool_name == "shell_execute":
        if config.WORKSPACE_DIRECTORY:
            args["directory"] = config.WORKSPACE_DIRECTORY
            args["timeout"] = 30

        else:
            logger.warning("MCP_SKILLS_PROVIDER_WORKSPACE_DIRECTORY not set")

    return None
    

root_agent = Agent(
    name=config.ADK_AGENT_NAME,
    model=config.ADK_AGENT_MODEL,
    description=config.ADK_AGENT_DESCRIPTION,
    instruction=config.ADK_AGENT_INSTRUCTION,
    tools=load_tools(),
    before_tool_callback=before_tool_callback
)


