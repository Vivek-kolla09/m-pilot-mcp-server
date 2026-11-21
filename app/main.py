
from mcp.server import MCPServer


from mcp.server.auth.middleware.auth_context import (
    AuthContextMiddleware,
    get_access_token,
)
from mcp.server.auth.middleware.bearer_auth import (
    BearerAuthBackend,
    RequireAuthMiddleware,
)
from starlette.middleware.authentication import AuthenticationMiddleware

from app.auth.firebase_token_verifier import FirebaseTokenVerifier
from app.tools.health.providers import register_health_tools
from app.tools.health.records import register_record_tools

# Initialize M-Pilot MCP server
mcp = MCPServer(
    "M-Pilot",
    instructions=(
        "M-Pilot is a modular multi-agent platform. "
        "Its first module provides health data tools."
    ),
)

# Register health-related MCP tools
register_health_tools(mcp)
register_record_tools(mcp)

@mcp.tool()
def test_connection() -> str:
    """Check whether the authenticated M-Pilot MCP server is working."""

    access_token = get_access_token()

    if access_token is None:
        raise RuntimeError("Authentication required.")

    return "Authenticated M-Pilot MCP server is running successfully!"


@mcp.tool()
def get_authenticated_user() -> dict:
    """Return the verified identity of the authenticated Firebase user."""

    access_token = get_access_token()

    if access_token is None or not access_token.subject:
        raise RuntimeError("Authenticated user identity unavailable.")

    return {
        "firebase_uid": access_token.subject,
    }


# Create the Starlette application with MCP's built-in lifespan
app = mcp.streamable_http_app()


# Register middleware from inner to outer.
# Starlette places each newly added middleware at the outside.

# app.add_middleware(
#     RequireAuthMiddleware,
#     required_scopes=[],
# )

app.add_middleware(AuthContextMiddleware)

app.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(
        FirebaseTokenVerifier(),
    ),
)

# Protect only the /mcp HTTP route.
app.routes[0].app = RequireAuthMiddleware(
    app.routes[0].app,
    required_scopes=[],
)