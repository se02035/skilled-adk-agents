import logging
import pathlib
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
except ImportError:
    import config

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
logger.info(config.ADK_AGENT_INSTRUCTION)


def load_skills(skills_parent_path: pathlib.Path) -> list[models.Skill]:
    """Load every ADK skill found in immediate subdirectories of a folder.

    For each child directory under ``skills_parent_path``, calls ``load_skill_from_dir``
    and collects the resulting ``models.Skill`` instance.

    Args:
        skills_parent_path: Path to a directory whose direct child folders are
            skill roots (each containing a skill definition, e.g. ``SKILL.md``).

    Returns:
        A list of ``models.Skill``, one entry per child directory that was loaded.
        The list is empty if there are no subdirectories or none load successfully.
    """
    loaded_skills = []

    # Iterate through the parent directory
    for skill_path in skills_parent_path.iterdir():
        # Check if the item is a folder
        if skill_path.is_dir():
            # Get the full absolute path as a string
            full_path = str(skill_path.resolve())

            # Load the Skill object and append it to our list
            skill = load_skill_from_dir(full_path)
            loaded_skills.append(skill)

            logger.info(f"Successfully loaded skill: {full_path}")

    return loaded_skills


def load_tools() -> list[ToolUnion]:
    """Assemble the tool list passed to the root agent (MCP toolsets).

    Currently registers: (1) a streamable-HTTP skills provider (``list_skills``,
    ``read_skill``, etc.) and (2) a stdio ``mcp-shell-server`` for ``shell_execute``.

    Returns:
        A list of ``BaseToolset`` instances (``MCPToolset``) configured from
        ``config`` (endpoints, workspace, shell allowlists, timeouts).
    """
    tools: list[BaseToolset] = []

    # ==============================
    # OPTION #1
    # USE THE ADK SKILLS FEATURE (RELOAD OF SKILLS IS NOT SUPPORTED CURENTLY)
    # ==============================
    # loaded_skills = load_skills(pathlib.Path(config.SKILLS_DIRECTORY))

    # if loaded_skills:
    #     tools.append(
    #         SkillToolset(
    #             skills=loaded_skills,
    #             code_executor=UnsafeLocalCodeExecutor())
    #             )

    # ==============================
    # OPTION #2
    # USE AN MCP SERVER TO PROVIDE SKILLS
    # ==============================
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

    shell_runner = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uvx",
                args=[
                    "--python",
                    "3.12",
                    "mcp-shell-server",
                ],
                env={
                    "ALLOW_COMMANDS": config.SHELL_RUNNER_ALLOWED_COMMANDS,
                    "ALLOW_PATTERNS": config.SHELL_RUNNER_ALLOWED_PATTERNS,
                },
            ),
            timeout=180,
        ),
        # Optional: Filter which tools from the MCP server are exposed
    )
    tools.append(shell_runner)

    return cast(list[ToolUnion], tools)


def before_tool_callback(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> dict[str, Any] | None:
    """Mutate tool call arguments before execution (workspace shell hardening).

    For ``shell_execute``, forces the working directory to ``config.WORKSPACE_DIRECTORY``,
    makes ``npx`` non-interactive, appends ``-y`` to ``npx`` ``skills add`` installs,
    and sets timeouts (including a longer cap for skill installs).

    Args:
        tool: The tool instance about to run.
        args: Mutable dict of argument names to values from the model; may be
            updated in place.
        tool_context: Runtime context (e.g. agent name); ``tool_context`` is not
            modified.

    Returns:
        ``None`` to proceed with the (possibly updated) ``args``. Return a dict
        only if the ADK contract requires replacing the tool result without invoking
        the tool (this implementation always returns ``None``).
    """
    tool_name = tool.name

    # there seems to be a glitch in the implementation around the directory parameter.
    # we want to ensure that the execution directory is set to the workspace directory.
    if tool_name == "shell_execute":
        if config.WORKSPACE_DIRECTORY:
            args["directory"] = config.WORKSPACE_DIRECTORY
            timeout_seconds = config.SHELL_RUNNER_TIMEOUT_SECONDS
            command = args.get("command", [])
            if isinstance(command, list) and command:
                # Make npx usage non-interactive to avoid TTY prompts.
                if command[0] == "npx" and "--yes" not in command and "-y" not in command:
                    command = ["npx", "--yes", *command[1:]]

                # Ensure skills installation never prompts for confirmation.
                if (
                    len(command) >= 4
                    and command[0] == "npx"
                    and command[2] == "skills"
                    and command[3] == "add"
                    and "-y" not in command
                ):
                    command.append("-y")
                args["command"] = command

            if (
                isinstance(command, list)
                and len(command) >= 4
                and command[0] == "npx"
                and command[2] == "skills"
                and command[3] == "add"
            ):
                timeout_seconds = config.SHELL_RUNNER_SKILLS_INSTALL_TIMEOUT_SECONDS
            args["timeout"] = timeout_seconds

        else:
            logger.warning("MCP_SKILLS_PROVIDER_WORKSPACE_DIRECTORY not set")

    return None


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """Configure HTTP retry and optional priority / paygo headers for each LLM request.

    Args:
        callback_context: ADK callback context for the current invocation.
        llm_request: The outbound request; ``config`` and ``http_options`` are
            created or updated on this object (retry policy, optional headers).

    Returns:
        ``None`` to send ``llm_request`` as updated. Return an ``LlmResponse``
        only to short-circuit the model call with a synthetic response.
    """
    # Ensure request config exists before adding transport settings.
    llm_request.config = llm_request.config or types.GenerateContentConfig()
    llm_request.config.http_options = llm_request.config.http_options or types.HttpOptions()

    llm_request.config.http_options.retry_options = types.HttpRetryOptions(
        attempts=config.ADK_AGENT_LLM_RETRY_ATTEMPTS,
        initial_delay=config.ADK_AGENT_LLM_RETRY_INITIAL_DELAY_SECONDS,
        max_delay=config.ADK_AGENT_LLM_RETRY_MAX_DELAY_SECONDS,
        exp_base=config.ADK_AGENT_LLM_RETRY_EXP_BASE,
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )

    # We want to use PrioPaygo (Paygo is not supported for litellm mode)
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
