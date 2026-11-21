
import getpass
import httpx


MCP_URL = "http://127.0.0.1:8001/mcp"


def main():
    token = getpass.getpass("Enter Firebase ID token (hidden): ")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-03-26",
    }

    with httpx.Client(timeout=20) as client:

        # Create an authenticated MCP session
        response = client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "security-test",
                        "version": "1.0.0",
                    },
                },
            },
        )

        response.raise_for_status()
        session_id = response.headers.get("mcp-session-id")

        if not session_id:
            print("Session creation failed.")
            return

        # Attempt to use the session without a bearer token
        unauthenticated_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-03-26",
            "Mcp-Session-Id": session_id,
        }

        response = client.post(
            MCP_URL,
            headers=unauthenticated_headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )

        print("Unauthenticated session request:", response.status_code)
        print("Response:", response.text[:300])

        print(
            "Session authentication enforcement:",
            "Passed" if response.status_code == 401 else "Needs investigation",
        )


if __name__ == "__main__":
    main()
