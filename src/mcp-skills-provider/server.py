from fastmcp.server.providers.skills.skill_provider import SkillResource
import asyncio
import logging

from pygments.token import String
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Skills Server")
mcp.add_provider(
    SkillsDirectoryProvider(
        roots=Path.home() / "Dev" / "demo-speckit-skills" / "asp" / ".agents" / "skills",
        reload=True,)
    )

@mcp.tool
async def list_skills() -> list:
    """
    List all available skills resource ids

    Returns a URI per skills (e.g. skill://my-skill/SKILL.md)
    """
    resources: list[SkillResource] = await mcp.providers[1].list_resources() 
    elements = []
    seen_names = set()

    for skill in resources:
        if skill.skill_info.name not in seen_names:
            elements.append({
                "uri": f"skill://{skill.skill_info.name}/SKILL.md", 
                "description": skill.skill_info.description,
                "name": skill.skill_info.name
            })
            seen_names.add(skill.skill_info.name)

    return elements

@mcp.tool
async def read_skill(skill_uri: str) -> String:
    """
    Read the skill based on the provided skills URI.
    
    Returns:
        the content of the skills SKILL.md file
    """
    skill: SkillResource = await mcp.providers[1].get_resource(skill_uri)
    content = await skill.read()

    return content

if __name__ == "__main__":
    PORT = 5555

    logger.info(f"MCP server started on port {PORT}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=PORT,
        )
    )