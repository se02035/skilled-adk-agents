import os
import logging
import asyncio
from dataclasses import dataclass
from fastmcp import FastMCP
from fastmcp.server.providers.skills.skill_provider import SkillResource, ResourceResult
from fastmcp.server.providers.skills import SkillsDirectoryProvider

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

SKILLS_DIRECTORY = os.getenv('SKILLS_DIRECTORY', 8001)

mcp = FastMCP("Skills Server")
mcp.add_provider(
    SkillsDirectoryProvider(roots=SKILLS_DIRECTORY,reload=True))

logger.info(f"Skills directory: {SKILLS_DIRECTORY}")


@dataclass
class SkillElement:
    uri: str
    description: str
    name: str
    root_directory: str


@mcp.tool
async def list_skills() -> list[SkillElement]:
    """
    List all available skills resource ids

    Returns a URI per skills (e.g. skill://my-skill/SKILL.md)
    """
    resources: list[SkillResource] = await mcp.list_resources()
    unique_skills: dict[str, SkillElement] = {}

    for resource in resources:
        info = resource.skill_info
        if info.name not in unique_skills:
            unique_skills[info.name] = SkillElement(
                uri=f"skill://{info.name}/SKILL.md", 
                description=info.description,
                name=info.name,
                root_directory=f"{SKILLS_DIRECTORY}/{info.name}"
            )

    return list(unique_skills.values())

@mcp.tool
async def read_skill(skill_uri: str) -> str:
    """
    Read the skill based on the provided skills URI.
    
    Returns:
        the content of the skills SKILL.md file
    """
    content: str = ""
    result: ResourceResult = await mcp.read_resource(skill_uri)

    if result: 
        content = result.contents[0].content
    else:
        content = f"Skill {skill_uri} not found"
    
    return content

if __name__ == "__main__":
    PORT = int(os.getenv('PORT', 5555))

    logger.info(f"MCP server listening on port {PORT}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=PORT,
        )
    )