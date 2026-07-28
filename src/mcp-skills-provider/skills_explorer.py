from __future__ import annotations

from fastmcp import FastMCP, FastMCPApp
from models import SkillElement
from prefab_ui.actions import SetState
from prefab_ui.actions.mcp import CallTool
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Button,
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
    Column,
    ForEach,
    Grid,
    Heading,
    Markdown,
    Muted,
    Row,
    Text,
)
from prefab_ui.components.control_flow import If
from prefab_ui.rx import RESULT, Rx
from skill_service import SkillService

_PREVIEW_MAX_CHARS = 120


def _description_preview(description: str) -> str:
    text = " ".join(description.split())
    if len(text) <= _PREVIEW_MAX_CHARS:
        return text
    truncated = text[:_PREVIEW_MAX_CHARS].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{truncated}..."


def create_skills_explorer(mcp: FastMCP, skill_service: SkillService) -> FastMCPApp:
    """Shared data tools for the agent + Prefab explorer UI for humans."""
    app = FastMCPApp("skills_explorer")

    @app.tool(model=True)
    async def list_skills() -> list[SkillElement]:
        """
        List all available skills resource ids

        Returns a URI per skills (e.g. skill://my-skill/SKILL.md)
        """
        return await skill_service.list_skills(mcp)

    @app.tool(model=True)
    async def read_skill(skill_uri: str) -> str:
        """
        Read the skill based on the provided skills URI.

        Returns:
            the content of the skills SKILL.md file
        """
        return await skill_service.read_skill(mcp, skill_uri)

    @app.ui()
    async def explore_skills() -> PrefabApp:
        """Browse available skills as tiles and open a skill's content."""
        skills = await skill_service.list_skills(mcp)
        rows = [
            {
                **skill.model_dump(),
                "description_preview": _description_preview(skill.description),
            }
            for skill in skills
        ]

        with PrefabApp(
            state={
                "skills": rows,
                "selected": None,
                "content": None,
                "loading": False,
            }
        ) as prefab:
            with Column(gap=4, css_class="p-6"):
                Heading("Skills")
                Muted("Open a skill to load SKILL.md content.")

                with Grid(min_column_width="16rem", gap=4):
                    with ForEach("skills") as skill:
                        with Card(css_class="h-full cursor-pointer"):
                            with CardHeader():
                                CardTitle(skill.name)
                            with CardContent():
                                Text(
                                    skill.description_preview,
                                    css_class=(
                                        "text-sm text-muted-foreground line-clamp-3"
                                    ),
                                )
                            with CardFooter():
                                with Column(gap=2, css_class="w-full"):
                                    Muted(skill.name)
                                    Button(
                                        "View details",
                                        variant="secondary",
                                        css_class="w-full",
                                        on_click=[
                                            SetState("selected", skill),
                                            SetState("content", None),
                                            SetState("loading", True),
                                            CallTool(
                                                read_skill,
                                                arguments={"skill_uri": skill.uri},
                                                on_success=[
                                                    SetState("content", RESULT),
                                                    SetState("loading", False),
                                                ],
                                                on_error=[
                                                    SetState(
                                                        "content",
                                                        "Failed to load skill content.",
                                                    ),
                                                    SetState("loading", False),
                                                ],
                                            ),
                                        ],
                                    )

                with If(Rx("selected")):
                    with Card():
                        with CardHeader():
                            with Row(gap=2, align="center"):
                                Heading(Rx("selected.name"), level=3)
                        with CardContent():
                            with Column(gap=2):
                                Muted(Rx("selected.uri"))
                                Text(Rx("selected.description"))
                                with If(Rx("loading")):
                                    Muted("Loading…")
                                with If(Rx("content")):
                                    Markdown(content=Rx("content"))

        return prefab

    return app
