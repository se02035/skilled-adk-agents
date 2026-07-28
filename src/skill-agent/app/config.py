from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from google.adk.models.lite_llm import LiteLlm

load_dotenv(Path(__file__).resolve().parent / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    """Parse common truthy string env values into a boolean."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


# config.py is at: <git_root>/src/skill-agent/app/config.py
GIT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_SKILLS_DIR = str(GIT_ROOT / ".agents" / "skills")

DESKTOP_COMMANDER_TOOL_FILTER = [
    "start_process",
    "interact_with_process",
    "read_process_output",
    "force_terminate",
]

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
     4. **Execute:** Perform the task strictly according to the selected skill documentation. If documentation requires shell usage, use `start_process`.

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
   - **Skills MCP (catalog and documentation):** Use ONLY `list_skills` and `read_skill` to discover skills, read SKILL.md instructions, and inspect skill metadata. Never use Desktop Commander to list, read, or browse `.agents/skills` or skill directories.
   - **Desktop Commander (shell execution only):** Use ONLY `start_process`, `interact_with_process`, `read_process_output`, and `force_terminate` to run commands after a skill instructs you to do so.
   - Never invent or call unavailable tool names (for example `shell_execute`, `read_file`, `list_directory`, `set_config_value`, `browser_navigate`).
   - For browser/web automation intents, first discover and read the appropriate skill via the Skills MCP, then execute its documented shell workflow via `start_process`.

6. **Desktop Commander Usage (shell only):**
   - Desktop Commander is NOT for skill discovery or reading skill files. It executes shell commands only.
   - Run skill scripts and CLI commands with `start_process`. The `command` argument is a single shell string, not an argv array.
   - Always set `timeout_ms` (milliseconds). Expect a practical ceiling near 60 seconds per call.
   - Commands run from the workspace directory automatically; use absolute paths when referencing files in shell commands.
   - When `read_skill` returns bash examples (for example `python scripts/foo.py`), translate them to `start_process` with the same command as a shell string.
   - For long-running commands, use `read_process_output` or `interact_with_process` after `start_process`.
   - Do not use `ls`, `cat`, `find`, or similar shell commands to explore skills — use `list_skills` and `read_skill` instead.

# AGENT SKILLS SPECIFICATION:
The complete agent skills specification can be found under: https://agentskills.io/llms.txt
Look up the specification to get more details around Skill resources like where to find skills scripts, assets, etc.
"""

ADK_AGENT_NAME = os.getenv("ADK_AGENT_NAME", "skill-assistant")
ADK_AGENT_MODEL = os.getenv("ADK_AGENT_MODEL", "gemini-2.5-flash")
ADK_AGENT_DESCRIPTION = os.getenv(
    "ADK_AGENT_DESCRIPTION",
    "A skills-based assistant. Skills MCP for discovery; Desktop Commander for shell only.",
)
SKILLS_DIRECTORY = os.getenv("SKILLS_DIRECTORY", DEFAULT_SKILLS_DIR)

SHELL_RUNNER_TIMEOUT_SECONDS = int(os.getenv("MCP_SHELL_RUNNER_TIMEOUT_SECONDS", "120"))
SHELL_RUNNER_SKILLS_INSTALL_TIMEOUT_SECONDS = int(
    os.getenv("MCP_SHELL_RUNNER_SKILLS_INSTALL_TIMEOUT_SECONDS", "600")
)
# MCP transport may cap tool calls near 60s regardless of this value.
SHELL_RUNNER_MAX_TIMEOUT_MS = int(os.getenv("MCP_SHELL_RUNNER_MAX_TIMEOUT_MS", "60000"))

MCP_SERVER_URL_SKILLS_PROVIDER = os.getenv("MCP_SKILLS_PROVIDER_ENDPOINT")

WORKSPACE_DIRECTORY = os.getenv("MCP_SKILLS_PROVIDER_WORKSPACE_DIRECTORY", str(GIT_ROOT))

# Uploaded attachments saved from unsupported Gemini inline mime types
ATTACHMENT_MAX_FILENAME_LENGTH = int(
    os.getenv("ATTACHMENT_MAX_FILENAME_LENGTH", "200")
)

DESKTOP_COMMANDER_CWD = Path(
    os.getenv("MCP_DESKTOP_COMMANDER_CWD", str(GIT_ROOT / ".desktop-commander"))
)
DESKTOP_COMMANDER_DEFAULT_SHELL = os.getenv(
    "MCP_DESKTOP_COMMANDER_DEFAULT_SHELL", "/bin/zsh"
)
DESKTOP_COMMANDER_BLOCKED_COMMANDS = _csv_list(
    os.getenv(
        "MCP_DESKTOP_COMMANDER_BLOCKED_COMMANDS",
        "rm -rf /,rm -rf ~,sudo,shutdown,reboot",
    )
)
DESKTOP_COMMANDER_ALLOWED_DIRECTORIES = _csv_list(
    os.getenv("MCP_DESKTOP_COMMANDER_ALLOWED_DIRECTORIES", str(GIT_ROOT))
) or [str(GIT_ROOT.resolve())]
DESKTOP_COMMANDER_TELEMETRY_ENABLED = _to_bool(
    os.getenv("MCP_DESKTOP_COMMANDER_TELEMETRY_ENABLED"), default=False
)

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


def ensure_desktop_commander_config() -> Path:
    """Ensure Desktop Commander config.json exists in the MCP subprocess cwd."""
    config_dir = DESKTOP_COMMANDER_CWD
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    if config_path.exists():
        return config_path

    payload = {
        "blockedCommands": DESKTOP_COMMANDER_BLOCKED_COMMANDS,
        "defaultShell": DESKTOP_COMMANDER_DEFAULT_SHELL,
        "allowedDirectories": [
            str(Path(path).resolve()) for path in DESKTOP_COMMANDER_ALLOWED_DIRECTORIES
        ],
        "telemetryEnabled": DESKTOP_COMMANDER_TELEMETRY_ENABLED,
    }
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path


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
    """Resolve the model passed to the root Agent."""
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
        custom_llm_provider="openai",
    )
