import asyncio
import os

from agent import root_agent
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# this is the port of the A2A server
A2A_HOST = os.getenv("A2A_HOST", "0.0.0.0")
A2A_PORT = int(os.getenv("A2A_PORT", 8001))
TUNNEL_ADDRESS = os.getenv("TUNNEL_ADDRESS", "")

a2a_agent_endpoint = f"http://{A2A_HOST}:{A2A_PORT}"
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
    uvicorn.run(a2a_app, host=A2A_HOST, port=A2A_PORT, log_level="info")
