
import getpass
import json
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

        # Initialize session
        initialize_payload = {
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

        response = client.post(
            MCP_URL,
            headers=headers,
            json=initialize_payload,
        )
        response.raise_for_status()

        session_id = response.headers.get("mcp-session-id")

        if not session_id:
            print("Session creation failed.")
            return

        headers["Mcp-Session-Id"] = session_id

        # Complete initialization
        client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
        )

        # Execute authenticated tool
        response = client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_authenticated_user",
                    "arguments": {},
                },
            },
        )

        print("Tool execution HTTP status:", response.status_code)

        if response.status_code != 200:
            print("Tool execution failed.")
            print(response.text[:500])
            return

        # Extract JSON-RPC response from SSE
        for line in response.text.splitlines():
            if line.startswith("data: "):
                result = json.loads(line[6:])

                if "error" in result:
                    print("MCP tool error:", result["error"])
                    return

                tool_result = result.get("result", {})
                content = tool_result.get("content", [])

                print("Tool execution successful:", True)

                for item in content:
                    if item.get("type") == "text":
                        data = json.loads(item["text"])
                        # print(
                        #     "Verified Firebase UID received:",
                        #     bool(data.get("firebase_uid")),
                        # )
                        print("Authenticated Firebase UID:", data.get("firebase_uid"))


if __name__ == "__main__":
    main()
