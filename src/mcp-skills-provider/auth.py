from fastmcp.server.auth.providers.google import GoogleTokenVerifier

from config import Settings


def build_auth(settings: Settings) -> GoogleTokenVerifier | None:
    """Return a Google token verifier when auth is enabled, else None."""
    if not settings.google_auth_enabled:
        return None

    # Basic Google token verifier (no aud claims validation).
    return GoogleTokenVerifier(
        required_scopes=["https://www.googleapis.com/auth/userinfo.profile"],
    )
