import asyncio
import getpass
import httpx

MCP_URL = "http://127.0.0.1:8001/mcp"


async def main():
    print("=== M-Pilot Cross-User Session Isolation Test ===")

    token_a = getpass.getpass("Enter User A Firebase ID token: ")
    token_b = getpass.getpass("Enter User B Firebase ID token: ")

    async with httpx.AsyncClient(timeout=30) as client:

        # Step 1: User A initializes an MCP session
        response_a = await client.post(
            MCP_URL,
            headers={
                "Authorization": f"Bearer {token_a}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-03-26",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "cross-user-test",
                        "version": "1.0.0",
                    },
                },
            },
        )

        print("\nUser A initialization status:", response_a.status_code)

        session_id = response_a.headers.get("Mcp-Session-Id")

        if response_a.status_code != 200 or not session_id:
            print("FAILED: User A could not create an MCP session.")
            return

        print("User A successfully created an MCP session.")

        # Step 2: User B attempts to access User A's session
        response_b = await client.post(
            MCP_URL,
            headers={
                "Authorization": f"Bearer {token_b}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-03-26",
                "Mcp-Session-Id": session_id,
            },
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )

        print("\nUser B access status:", response_b.status_code)

        if response_b.status_code == 404:
            print("\nPASS: User B cannot access User A's MCP session.")
        else:
            print("\nFAIL: Unexpected response from the MCP server.")

        # Step 3: User A verifies their own session still works
        response_a_again = await client.post(
            MCP_URL,
            headers={
                "Authorization": f"Bearer {token_a}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-03-26",
                "Mcp-Session-Id": session_id,
            },
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
                "params": {},
            },
        )

        print("\nUser A access status:", response_a_again.status_code)

        if response_a_again.status_code == 200:
            print("PASS: User A can still access their own session.")
        else:
            print("FAIL: User A could not access their own session.")


if __name__ == "__main__":
    asyncio.run(main())