import asyncio

from app.main import app


async def main():
    print("Entering MCP lifespan...")

    async with app.router.lifespan_context(app):
        print("MCP lifespan started successfully.")

    print("MCP lifespan shut down successfully.")


if __name__ == "__main__":
    asyncio.run(main())