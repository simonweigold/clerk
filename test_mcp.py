import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    print("mcp imported successfully")

if __name__ == "__main__":
    asyncio.run(main())
