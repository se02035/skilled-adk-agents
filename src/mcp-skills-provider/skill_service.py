import logging
from typing import cast

from config import Settings
from fastmcp import FastMCP
from fastmcp.resources import ResourceResult
from fastmcp.server.providers.skills.skill_provider import SkillResource
from models import SkillElement

logger = logging.getLogger(__name__)


class SkillService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def list_skills(self, mcp: FastMCP) -> list[SkillElement]:
        resources = cast(list[SkillResource], await mcp.list_resources())
        unique_skills: dict[str, SkillElement] = {}
        skills_dir = self._settings.skills_directory

        for resource in resources:
            info = resource.skill_info
            if info.name not in unique_skills:
                unique_skills[info.name] = SkillElement(
                    uri=f"skill://{info.name}/SKILL.md",
                    description=info.description,
                    name=info.name,
                    root_directory=f"{skills_dir}/{info.name}",
                )

        return list(unique_skills.values())

    async def read_skill(self, mcp: FastMCP, skill_uri: str) -> str:
        normalized_uri = skill_uri.strip()

        # Most callers should pass an exact URI from list_skills. If they provide
        # a provider-specific URI (e.g. skill://org/repo/skill/SKILL.md), try to
        # recover by matching the trailing skill name.
        try:
            result: ResourceResult = await mcp.read_resource(normalized_uri)
            if result:
                return self._text_content(result.contents[0].content)
        except Exception:
            pass

        resources = cast(list[SkillResource], await mcp.list_resources())
        by_name: dict[str, str] = {}
        for resource in resources:
            info = resource.skill_info
            by_name[info.name.lower()] = f"skill://{info.name}/SKILL.md"

        for candidate in self._fallback_candidates(normalized_uri):
            resolved_uri = by_name.get(candidate.lower())
            if not resolved_uri:
                continue
            result = await mcp.read_resource(resolved_uri)
            if result:
                logger.info(
                    "Resolved unknown skill URI %s -> %s",
                    normalized_uri,
                    resolved_uri,
                )
                return self._text_content(result.contents[0].content)

        return (
            f"Skill {skill_uri} not found. Call list_skills and pass an exact URI from that result."
        )

    @staticmethod
    def _text_content(data: str | bytes) -> str:
        if isinstance(data, bytes):
            return data.decode()
        return data

    @staticmethod
    def _fallback_candidates(normalized_uri: str) -> list[str]:
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
        return candidates
