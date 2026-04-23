import asyncio
import logging
import os
from typing import cast

from fastmcp import FastMCP
from fastmcp.resources.resource import ResourceResult
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from fastmcp.server.providers.skills.skill_provider import SkillResource
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

_DEFAULT_SKILLS_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".agents", "skills")
)
SKILLS_DIRECTORY = os.getenv("SKILLS_DIRECTORY", _DEFAULT_SKILLS_DIRECTORY)

mcp = FastMCP("Skills Server")
mcp.add_provider(SkillsDirectoryProvider(roots=SKILLS_DIRECTORY, reload=True))

logger.info(f"Skills directory: {SKILLS_DIRECTORY}")


def _text_content(data: str | bytes) -> str:
    if isinstance(data, bytes):
        return data.decode()
    return data


class SkillElement(BaseModel):
    """
    Represents a discovered agent skill and its metadata.
    Review the description and name to decide if you want to use this skill.
    """

    uri: str = Field(
        description="The unique URI for the skill. Pass this exact URI to the read_skill tool to get its instructions."
    )
    description: str = Field(
        description="A brief explanation of what the skill does and when it should be used."
    )
    name: str = Field(description="The unique name identifying the skill.")
    root_directory: str = Field(
        description="The absolute path to the skill's root directory on the local file system."
    )


@mcp.tool
async def list_skills() -> list[SkillElement]:
    """
    List all available skills resource ids

    Returns a URI per skills (e.g. skill://my-skill/SKILL.md)
    """
    resources = cast(list[SkillResource], await mcp.list_resources())
    unique_skills: dict[str, SkillElement] = {}

    for resource in resources:
        info = resource.skill_info
        if info.name not in unique_skills:
            unique_skills[info.name] = SkillElement(
                uri=f"skill://{info.name}/SKILL.md",
                description=info.description,
                name=info.name,
                root_directory=f"{SKILLS_DIRECTORY}/{info.name}",
            )

    return list(unique_skills.values())


@mcp.tool
async def read_skill(skill_uri: str) -> str:
    """
    Read the skill based on the provided skills URI.

    Returns:
        the content of the skills SKILL.md file
    """
    normalized_uri = skill_uri.strip()

    # Most callers should pass an exact URI from list_skills. If they provide
    # a provider-specific URI (e.g. skill://org/repo/skill/SKILL.md), try to
    # recover by matching the trailing skill name.
    try:
        result: ResourceResult = await mcp.read_resource(normalized_uri)
        if result:
            return _text_content(result.contents[0].content)
    except Exception:
        pass

    resources = cast(list[SkillResource], await mcp.list_resources())
    by_name: dict[str, str] = {}
    for resource in resources:
        info = resource.skill_info
        by_name[info.name.lower()] = f"skill://{info.name}/SKILL.md"

    # Fallback candidate extraction for URIs like:
    # - skill://mindrally/skills/web-scraping/SKILL.md
    # - skill://jamditis/claude-skills-journalism@web-scraping/SKILL.md
    path = normalized_uri.replace("skill://", "").strip("/")
    parts = [p for p in path.split("/") if p and p != "SKILL.md"]
    candidates: list[str] = []
    if parts:
        candidates.append(parts[-1])
    if "@" in path:
        candidates.append(path.rsplit("@", 1)[-1].replace("/SKILL.md", ""))

    for candidate in candidates:
        resolved_uri = by_name.get(candidate.lower())
        if not resolved_uri:
            continue
        result = await mcp.read_resource(resolved_uri)
        if result:
            logger.info("Resolved unknown skill URI %s -> %s", normalized_uri, resolved_uri)
            return _text_content(result.contents[0].content)

    return f"Skill {skill_uri} not found. Call list_skills and pass an exact URI from that result."


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 5555))

    logger.info(f"MCP server listening on port {PORT}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=PORT,
        )
    )
