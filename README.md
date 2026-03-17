# README

## Skills
```sh
npx skills add miticojo/adk-skill
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```


## Setup
```sh
sudo ./devcontainer/scripts/install-dependencies.sh
```

## Create ADK Agent 



```sh
AGENT_TEMPLATE_DIR=.context/examples/agent_template
OUTPUT_DIR=src
OUTPUT_AGENT_NAME=my-test-agent

# create a template based ADK agent
uvx agent-starter-pack create $OUTPUT_DIR/$OUTPUT_AGENT_NAME -a local@$AGENT_TEMPLATE_DIR
```

## Run

### A2A Server

#### Setup Tunnel

```sh
A2A_PORT=8001
npx ngrok http $A2A_PORT --host-header="localhost:$A2A_PORT"

# copy the ngrok service URL (e.g. https://SOMETHING.ngrok-free.dev) and update the TUNNEL_ADDRESS in the .env file
```

#### Start A2A Server

```sh
cd src/skill-agent
uv run python app/a2a_agent.py
```