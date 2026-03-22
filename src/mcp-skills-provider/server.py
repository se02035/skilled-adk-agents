import os
import logging
import asyncio
from pydantic import BaseModel, Field
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

class SkillElement(BaseModel):
    """
    Represents a discovered agent skill and its metadata. 
    Review the description and name to decide if you want to use this skill.
    """
    uri: str = Field(description="The unique URI for the skill. Pass this exact URI to the read_skill tool to get its instructions.")
    description: str = Field(description="A brief explanation of what the skill does and when it should be used.")
    name: str = Field(description="The unique name identifying the skill.")
    root_directory: str = Field(description="The absolute path to the skill's root directory on the local file system.")

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