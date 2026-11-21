
from mcp.server import MCPServer

# Initialize the M-Pilot MCP server
mcp = MCPServer(
    "M-Pilot",
    instructions=(
        "M-Pilot is a modular multi-agent platform. "
        "Its first module provides health data tools."
    ),
)


@mcp.tool()
def test_connection() -> str:
    """Check whether the M-Pilot MCP server is working."""
    return "M-Pilot MCP server is running successfully!"


if __name__ == "__main__":
    mcp.run(transport="stdio")


# What this code does
# - MCPServer("M-Pilot") creates your MCP server.
# - @mcp.tool() registers a tool that AI agents can discover and call.
# - test_connection() is our first test tool.
# - stdio provides local communication between an MCP host and the server.
