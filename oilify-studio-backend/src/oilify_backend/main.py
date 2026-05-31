import uvicorn

from .api.app import create_app
from .config import get_settings

app = create_app()


def main() -> None:
    """Start the Oilify API server."""

    settings = get_settings()

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.RELOAD_APP_ON_CHANGE,
    )


if __name__ == "__main__":
    main()
