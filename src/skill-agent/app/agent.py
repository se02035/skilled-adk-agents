import logging
import pathlib
import re
from pathlib import Path
from typing import Any, cast

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import ToolUnion
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.skills import load_skill_from_dir, models
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StreamableHTTPConnectionParams,
)
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from mcp import StdioServerParameters

try:
    from . import config
    from .attachments import sanitize_unsupported_inline_attachments
except ImportError:
    import config
    from attachments import sanitize_unsupported_inline_attachments

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
logger.info(config.ADK_AGENT_INSTRUCTION)


def load_skills(skills_parent_path: pathlib.Path) -> list[models.Skill]:
    """Load every ADK skill found in immediate subdirectories of a folder."""
    loaded_skills = []

    for skill_path in skills_parent_path.iterdir():
        if skill_path.is_dir():
            full_path = str(skill_path.resolve())
            skill = load_skill_from_dir(full_path)
            loaded_skills.append(skill)
            logger.info(f"Successfully loaded skill: {full_path}")

    return loaded_skills


def _harden_npx_command(command: str) -> str:
    """Make npx invocations non-interactive for skills installs."""
    stripped = command.strip()
    if not stripped.startswith("npx"):
        return command

    if not re.search(r"(?:^|\s)(?:--yes|-y)(?:\s|$)", stripped):
        stripped = re.sub(r"^npx\s+", "npx --yes ", stripped, count=1)

    if re.search(r"\bskills\s+add\b", stripped) and not re.search(
        r"(?:^|\s)-y(?:\s|$)", stripped
    ):
        stripped = stripped.rstrip() + " -y"

    return stripped


def _is_skills_install(command: str) -> bool:
    return bool(re.search(r"\bnpx\b.*\bskills\s+add\b", command))


def _wrap_workspace_command(command: str, workspace: str) -> str:
    workspace_path = str(Path(workspace).resolve())
    cmd = command.strip()
    if cmd.startswith(f"cd {workspace_path}") or cmd.startswith(f"cd '{workspace_path}'"):
        return cmd
    return f"cd {workspace_path} && {cmd}"


def load_tools() -> list[ToolUnion]:
    """Assemble the tool list passed to the root agent (MCP toolsets).

    Currently registers: (1) a streamable-HTTP skills provider (``list_skills``,
    ``read_skill``) and (2) Desktop Commander for shell execution only.
    """
    tools: list[BaseToolset] = []

    skills_url = config.MCP_SERVER_URL_SKILLS_PROVIDER
    if not skills_url:
        msg = (
            "MCP_SKILLS_PROVIDER_ENDPOINT must be set to use the streamable-HTTP skills MCP toolset"
        )
        raise ValueError(msg)

    skills_provider = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=skills_url,
            timeout=180,
        ),
    )
    tools.append(skills_provider)

    config.ensure_desktop_commander_config()

    desktop_commander = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@wonderwhy-er/desktop-commander@latest",
                    "--no-onboarding",
                ],
                cwd=str(config.DESKTOP_COMMANDER_CWD),
                env={
                    "NODE_NO_WARNINGS": "1",
                },
            ),
            timeout=180,
        ),
        tool_filter=config.DESKTOP_COMMANDER_TOOL_FILTER,
    )
    tools.append(desktop_commander)

    return cast(list[ToolUnion], tools)


def before_tool_callback(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> dict[str, Any] | None:
    """Mutate tool call arguments before execution (workspace shell hardening).

    For ``start_process``, forces commands to run from the workspace directory,
    makes ``npx`` non-interactive, and sets ``timeout_ms``.
    """
    tool_name = tool.name

    if tool_name == "start_process":
        if not config.WORKSPACE_DIRECTORY:
            logger.warning("MCP_SKILLS_PROVIDER_WORKSPACE_DIRECTORY not set")
            return None

        command = args.get("command", "")
        if isinstance(command, str) and command.strip():
            command = _harden_npx_command(command)
            command = _wrap_workspace_command(command, config.WORKSPACE_DIRECTORY)
            args["command"] = command

        timeout_seconds = config.SHELL_RUNNER_TIMEOUT_SECONDS
        if isinstance(command, str) and _is_skills_install(command):
            timeout_seconds = config.SHELL_RUNNER_SKILLS_INSTALL_TIMEOUT_SECONDS

        timeout_ms = min(
            timeout_seconds * 1000,
            config.SHELL_RUNNER_MAX_TIMEOUT_MS,
        )
        args["timeout_ms"] = timeout_ms

        if config.DESKTOP_COMMANDER_DEFAULT_SHELL:
            args.setdefault("shell", config.DESKTOP_COMMANDER_DEFAULT_SHELL)

    return None


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """Configure HTTP retry and optional priority / paygo headers for each LLM request."""
    sanitize_unsupported_inline_attachments(llm_request)

    llm_request.config = llm_request.config or types.GenerateContentConfig()
    llm_request.config.http_options = llm_request.config.http_options or types.HttpOptions()

    llm_request.config.http_options.retry_options = types.HttpRetryOptions(
        attempts=config.ADK_AGENT_LLM_RETRY_ATTEMPTS,
        initial_delay=config.ADK_AGENT_LLM_RETRY_INITIAL_DELAY_SECONDS,
        max_delay=config.ADK_AGENT_LLM_RETRY_MAX_DELAY_SECONDS,
        exp_base=config.ADK_AGENT_LLM_RETRY_EXP_BASE,
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )

    if config.ADK_AGENT_PRIORITY_PAYGO_ENABLED and not config.is_litellm_mode():
        headers = llm_request.config.http_options.headers or {}
        headers[config.ADK_AGENT_PRIORITY_PAYGO_HEADER_NAME] = (
            config.ADK_AGENT_PRIORITY_PAYGO_HEADER_VALUE
        )
        llm_request.config.http_options.headers = headers

    return None


_agent_model = config.resolve_agent_model()
if config.is_litellm_mode():
    logger.info(
        "LiteLLM proxy: base=%s model=%s",
        config.LITELLM_API_BASE,
        config.LITELLM_MODEL,
    )

root_agent = Agent(
    name=config.ADK_AGENT_NAME,
    model=_agent_model,
    description=config.ADK_AGENT_DESCRIPTION,
    instruction=config.ADK_AGENT_INSTRUCTION,
    tools=load_tools(),
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
)
