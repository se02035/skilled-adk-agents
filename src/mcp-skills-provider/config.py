import os
from dataclasses import dataclass

_DEFAULT_SKILLS_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".agents", "skills")
)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    skills_directory: str
    google_auth_enabled: bool
    port: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            skills_directory=os.getenv("SKILLS_DIRECTORY", _DEFAULT_SKILLS_DIRECTORY),
            google_auth_enabled=_env_bool("MCP_GOOGLE_AUTH_ENABLED", default=False),
            port=int(os.getenv("PORT", "5555")),
        )
