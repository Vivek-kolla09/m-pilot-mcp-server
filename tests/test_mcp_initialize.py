
import getpass
import httpx


MCP_URL = "http://127.0.0.1:8001/mcp"


def main():
    token = getpass.getpass("Enter Firebase ID token (hidden): ")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "m-pilot-test-client",
                "version": "1.0.0",
            },
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    response = httpx.post(
        MCP_URL,
        headers=headers,
        json=payload,
        timeout=20,
    )

    print("HTTP Status:", response.status_code)
    print("Response:", response.text[:1500])

    session_id = response.headers.get("mcp-session-id")

    if session_id:
        print("MCP session established:", True)
    else:
        print("MCP session established:", False)


if __name__ == "__main__":
    main()

