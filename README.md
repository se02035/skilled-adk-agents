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

# /Users/oliverli/Dev/demo-speckit-skills/asp/.context/examples/agent_template
# /Users/oliverli/Dev/demo-speckit-skills/asp/.context/agent_template
# /Users/oliverli/Dev/demo-speckit-skills/asp/.context/examples/agent_template/.context/agent_template