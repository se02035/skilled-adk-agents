"""
Filename: a2a_agent.py
Author: Oliver Lintner  
Date: 2026-02-22
Version: 1.0
Description: 
    This script demonstrates a sample A2A server for ADK agent (called 'root_agent'). 
    It uses the to_a2a function to convert an ADK agent to an A2A app.

Validation:
    Run the A2A server and issue a HTTP request (e.g. usign `curl`) to it. The response must contain a valid 
    A2A agent card following the A2A spec defined in https://a2a-protocol.org/latest/definitions/#json

License: MIT License
Contact: [EMAIL_ADDRESS]
Dependencies: google.adk.a2a.utils.agent_to_a2a, agent, uvicorn
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from agent import root_agent

load_dotenv()

# this is the port of the A2A server
A2A_PORT = int(os.getenv('A2A_PORT', 8001))
TUNNEL_ADDRESS = os.getenv('TUNNEL_ADDRESS', '')

a2a_agent_endpoint = f"http://localhost:{A2A_PORT}"
if TUNNEL_ADDRESS:
    a2a_agent_endpoint = f"{TUNNEL_ADDRESS}"

# create the AgentCard & update the URL (if a tunnel has been specified)
card_builder = AgentCardBuilder(agent=root_agent, rpc_url=a2a_agent_endpoint)
card = asyncio.run(card_builder.build())

# convert the ADK agent to an A2A app
a2a_app = to_a2a(root_agent, port=A2A_PORT, agent_card=card)

if __name__ == "__main__":
    import uvicorn
    # run the A2A server
    uvicorn.run(a2a_app, host="0.0.0.0", port=A2A_PORT, log_level="info")