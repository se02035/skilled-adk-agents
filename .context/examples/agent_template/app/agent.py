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

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from tools.sample_weather_tool import get_weather

load_dotenv()

ADK_AGENT_NAME = os.getenv('ADK_AGENT_NAME')
ADK_AGENT_MODEL = os.getenv('ADK_AGENT_MODEL')
ADK_AGENT_INSTRUCTION = os.getenv('ADK_AGENT_INSTRUCTION')
ADK_AGENT_DESCRIPTION = os.getenv('ADK_AGENT_DESCRIPTION')

root_agent = Agent(
    name=ADK_AGENT_NAME,
    model=ADK_AGENT_MODEL,
    description=ADK_AGENT_DESCRIPTION,
    instruction=ADK_AGENT_INSTRUCTION,
    tools=[get_weather],
)