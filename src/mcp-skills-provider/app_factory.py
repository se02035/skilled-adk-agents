import logging

from auth import build_auth
from config import Settings
from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from skill_service import SkillService
from skills_explorer import create_skills_explorer

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastMCP:
    mcp = FastMCP("Skills Server", auth=build_auth(settings))
    mcp.add_provider(SkillsDirectoryProvider(roots=settings.skills_directory, reload=True))

    skill_service = SkillService(settings)
    mcp.add_provider(create_skills_explorer(mcp, skill_service))

    logger.info("Skills directory: %s", settings.skills_directory)
    if settings.google_auth_enabled:
        logger.info("Google token verification enabled")
    else:
        logger.warning("MCP auth disabled — HTTP requests will not require a Bearer token")

    return mcp
