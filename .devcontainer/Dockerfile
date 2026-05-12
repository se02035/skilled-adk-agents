# Local dev image: Python (devcontainer base) + Node (Gemini CLI & agents-cli skills) + uv + Google tooling
# References: https://google.github.io/agents-cli/ | https://geminicli.com/
# Podman (host): set Cursor/VS Code setting dev.containers.dockerPath to "podman".
# Docker Engine 29 + old Dev Containers CLI: update Dev Containers (Cursor: anysphere.remote-containers with CLI >= 0.80.2). See WORKAROUND-DOCKER29.txt.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

USER root

# The devcontainers Python image may include dl.yarnpkg.com; its repo key can go stale and breaks apt-get update.
RUN rm -f /etc/apt/sources.list.d/*yarn* 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
  && mkdir -p /etc/apt/keyrings \
  && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
  && apt-get update && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# https://docs.astral.sh/uv/
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Gemini CLI: https://geminicli.com/
RUN npm install -g @google/gemini-cli

USER vscode
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Google Agents CLI: https://google.github.io/agents-cli/
RUN uv tool install google-agents-cli \
  && agents-cli setup --skip-auth