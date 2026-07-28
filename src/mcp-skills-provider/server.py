import asyncio
import logging

from app_factory import create_app
from config import Settings

logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings.from_env()
mcp = create_app(settings)


def main() -> None:
    logger.info("MCP server listening on port %s", settings.port)
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=settings.port,
        )
    )


if __name__ == "__main__":
    main()
