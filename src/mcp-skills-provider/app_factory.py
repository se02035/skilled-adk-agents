import logging

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

from auth import build_auth
from config import Settings
from models import SkillElement
from skill_service import SkillService

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastMCP:
    mcp = FastMCP("Skills Server", auth=build_auth(settings))
    mcp.add_provider(
        SkillsDirectoryProvider(roots=settings.skills_directory, reload=True)
    )

    skill_service = SkillService(settings)

    logger.info("Skills directory: %s", settings.skills_directory)
    if settings.google_auth_enabled:
        logger.info("Google token verification enabled")
    else:
        logger.warning(
            "MCP auth disabled — HTTP requests will not require a Bearer token"
        )

    @mcp.tool
    async def list_skills() -> list[SkillElement]:
        """
        List all available skills resource ids

        Returns a URI per skills (e.g. skill://my-skill/SKILL.md)
        """
        return await skill_service.list_skills(mcp)

    @mcp.tool
    async def read_skill(skill_uri: str) -> str:
        """
        Read the skill based on the provided skills URI.

        Returns:
            the content of the skills SKILL.md file
        """
        return await skill_service.read_skill(mcp, skill_uri)

    return mcp
