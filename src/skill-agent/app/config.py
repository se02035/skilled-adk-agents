from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from google.adk.models.lite_llm import LiteLlm

load_dotenv(Path(__file__).resolve().parent / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    """Parse common truthy string env values into a boolean.

    Args:
        value: Raw string from the environment, or ``None`` if unset.
        default: Value to return when ``value`` is ``None`` or empty after strip.

    Returns:
        ``True`` if ``value`` (case-insensitive, stripped) is one of
        ``1``, ``true``, ``yes``, or ``on``; otherwise ``False`` unless
        ``value`` is ``None``, in which case ``default`` is returned.
    """
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Determine the git root directory based on the location of config.py
# config.py is at: <git_root>/src/skill-agent/app/config.py
GIT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_SKILLS_DIR = str(GIT_ROOT / ".agents" / "skills")

ADK_AGENT_INSTRUCTION = """
#AGENT INSTRUCTIONS:
You are a highly capable AI assistant equipped with an extensible skill system. Your objective is to fulfill user requests by effectively leveraging these specialized tools.

**TASK HANDLING POLICY:**
0. **Plan First (Always):**
   - Before executing substantial work, first provide a concise plan tailored to the user's request.
   - The plan should include intended steps, required tools/skills, and any external actions.
   - If the user approves, proceed. If the user redirects, revise the plan.

1. **Basic Tasks (No Special Skill Needed):**
   - For common tasks (for example: text summarization, rewriting, drafting, translation, brainstorming, or basic analysis), help the user directly using your general capabilities.
   - Only use a skill for these tasks when the user explicitly asks for a specific skill-based workflow.

2. **Specialized Tasks (Skill-First Required):**
   - For specialized, multi-step, or tool-heavy tasks (for example: external integrations, web automation, file conversions, advanced document workflows, API/platform specific operations), you must follow this workflow:
     1. **Discover:** Start by calling `list_skills` to retrieve the current skill catalog.
     2. **Assess & Inspect:** Evaluate relevance, choose the best candidate, and call `read_skill` for that skill before execution.
     3. **Fallback (Missing Skills):** If no suitable skill exists:
        - Inform the user you are searching for an appropriate skill.
        - Call `read_skill` for the `find-skills` skill to review its instructions.
        - Execute the find-skills workflow to locate the best matching capability for the user's intent.
        - When evaluating search results, prioritize quality in this order:
          1. Prefer skills with high adoption (ideally 1000+ installs).
          2. Prefer skills from well-known and trusted organizations, especially Anthropic, OpenAI, Google, and Microsoft.
          3. If multiple options match, propose the highest-install trusted-source option first, then alternatives.
        - If only low-install or unknown-source skills are available, explicitly warn the user before recommending or installing.
        - If installing an external skill is needed, ask for explicit user permission before running any install command.
     4. **Execute:** Perform the task strictly according to the selected skill documentation. If documentation requires shell usage, use the `shell_runner` tool.

3. **Always Prefer Intent Coverage:**
   - If the user's intent is specialized and no installed skill is sufficient, attempt to find and add a relevant skill before giving up.
   - If no appropriate skill can be found, clearly explain this and then provide the best possible direct assistance.

4. **Permission Gate for Impactful Actions:**
   - Always ask for explicit user confirmation before:
     - Installing or updating external skills/packages.
     - Running commands that modify the environment, filesystem, or system configuration.
     - Triggering external side effects (sending emails/messages, uploads, API mutations, deployments).
   - If permission is not granted, do not execute the action; offer a safe alternative.

5. **Tool Calling Safety (Critical):**
   - You may call ONLY tools that are actually registered in this agent runtime.
   - In this environment, valid callable tools are: `list_skills`, `read_skill`, and `shell_execute`.
   - Never invent or call tool names like browser APIs directly (for example `browser_navigate`).
   - For browser/web automation intents, first discover and read the appropriate skill, then execute its documented shell workflow via `shell_execute`.

# AGENT SKILLS SPECIFICATION:
The complete agent skills specification can be found under: https://agentskills.io/llms.txt
Look up the specification to get more details around Skill resources like where to find skills scripts, assets, etc.
"""

ADK_AGENT_NAME = os.getenv("ADK_AGENT_NAME", "skill-assistant")
ADK_AGENT_MODEL = os.getenv("ADK_AGENT_MODEL", "gemini-2.5-flash")
ADK_AGENT_DESCRIPTION = os.getenv("ADK_AGENT_DESCRIPTION", "A skills-based assistant.")
SKILLS_DIRECTORY = os.getenv("SKILLS_DIRECTORY", DEFAULT_SKILLS_DIR)

SHELL_RUNNER_ALLOWED_COMMANDS = os.getenv("MCP_SHELL_RUNNER_ALLOWED_COMMANDS", "")
SHELL_RUNNER_ALLOWED_PATTERNS = os.getenv("MCP_SHELL_RUNNER_ALLOWED_PATTERNS", "")
SHELL_RUNNER_TIMEOUT_SECONDS = int(os.getenv("MCP_SHELL_RUNNER_TIMEOUT_SECONDS", "120"))
SHELL_RUNNER_SKILLS_INSTALL_TIMEOUT_SECONDS = int(
    os.getenv("MCP_SHELL_RUNNER_SKILLS_INSTALL_TIMEOUT_SECONDS", "600")
)

MCP_SERVER_URL_SKILLS_PROVIDER = os.getenv("MCP_SKILLS_PROVIDER_ENDPOINT")

WORKSPACE_DIRECTORY = os.getenv("MCP_SKILLS_PROVIDER_WORKSPACE_DIRECTORY", GIT_ROOT)

# LLM call behavior
ADK_AGENT_PRIORITY_PAYGO_ENABLED = _to_bool(
    os.getenv("ADK_AGENT_PRIORITY_PAYGO_ENABLED"), default=True
)
ADK_AGENT_PRIORITY_PAYGO_HEADER_NAME = os.getenv(
    "ADK_AGENT_PRIORITY_PAYGO_HEADER_NAME", "X-Vertex-AI-LLM-Shared-Request-Type"
)
ADK_AGENT_PRIORITY_PAYGO_HEADER_VALUE = os.getenv(
    "ADK_AGENT_PRIORITY_PAYGO_HEADER_VALUE", "priority"
)
ADK_AGENT_LLM_RETRY_ATTEMPTS = int(os.getenv("ADK_AGENT_LLM_RETRY_ATTEMPTS", "5"))
ADK_AGENT_LLM_RETRY_INITIAL_DELAY_SECONDS = float(
    os.getenv("ADK_AGENT_LLM_RETRY_INITIAL_DELAY_SECONDS", "1.0")
)
ADK_AGENT_LLM_RETRY_MAX_DELAY_SECONDS = float(
    os.getenv("ADK_AGENT_LLM_RETRY_MAX_DELAY_SECONDS", "30.0")
)
ADK_AGENT_LLM_RETRY_EXP_BASE = float(os.getenv("ADK_AGENT_LLM_RETRY_EXP_BASE", "2.0"))

# LiteLLM proxy (used when ADK_AGENT_MODEL=litellm)
LITELLM_API_BASE = os.getenv("LITELLM_API_BASE")
LITELLM_MODEL = os.getenv("LITELLM_MODEL")
LITELLM_VIRTUAL_KEY = os.getenv("LITELLM_VIRTUAL_KEY")


def is_litellm_mode() -> bool:
    """Return True when ADK_AGENT_MODEL selects the LiteLLM proxy backend."""
    return ADK_AGENT_MODEL.strip().lower() == "litellm"


def _normalize_litellm_api_base(api_base: str) -> str:
    """Normalize a LiteLLM proxy base URL for OpenAI-compatible routing."""
    normalized = api_base.rstrip("/")
    if normalized.endswith("/v1"):
        normalized = normalized[:-3]
    return normalized


def resolve_agent_model() -> str | LiteLlm:
    """Resolve the model passed to the root Agent.

    When ``ADK_AGENT_MODEL`` is ``litellm`` (case-insensitive), returns a
    ``LiteLlm`` wrapper configured from ``LITELLM_*`` env vars. Otherwise
    returns ``ADK_AGENT_MODEL`` as a native ADK model id string.

    In LiteLLM mode, set ``LITELLM_MODEL`` to the exact **Model Name** shown in
    the LiteLLM Model Management UI (e.g. ``ollama/gemma3:4b.ollama``,
    ``gemini-2.5-flash``, ``gemini-3.1-pro-preview``). Any model registered on
    the proxy works; the virtual key must be allowed to access that model.
    """
    if not is_litellm_mode():
        return ADK_AGENT_MODEL

    api_base = LITELLM_API_BASE
    model = LITELLM_MODEL
    virtual_key = LITELLM_VIRTUAL_KEY

    missing = [
        name
        for name, val in [
            ("LITELLM_API_BASE", api_base),
            ("LITELLM_MODEL", model),
            ("LITELLM_VIRTUAL_KEY", virtual_key),
        ]
        if not val
    ]
    if missing:
        msg = f"ADK_AGENT_MODEL=litellm requires: {', '.join(missing)}"
        raise ValueError(msg)
    if api_base is None or model is None or virtual_key is None:
        msg = (
            "ADK_AGENT_MODEL=litellm requires LITELLM_API_BASE, LITELLM_MODEL, LITELLM_VIRTUAL_KEY"
        )
        raise ValueError(msg)

    from google.adk.models.lite_llm import LiteLlm

    return LiteLlm(
        model=model,
        api_base=_normalize_litellm_api_base(api_base),
        api_key=virtual_key,
        # Route through the proxy's OpenAI-compatible API, not native provider APIs
        # (e.g. Ollama /api/generate) inferred from model names like gemma3:4b.ollama.
        custom_llm_provider="openai",
    )
