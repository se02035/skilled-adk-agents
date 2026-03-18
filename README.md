# README

## Skills
```sh
npx skills add miticojo/adk-skill
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```


## Setup

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