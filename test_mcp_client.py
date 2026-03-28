import asyncio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def main():
    url = "http://localhost:8200/mcp/sse"
    print(f"Connecting to Fenrir MCP SSE endpoint at {url}...")
    
    try:
        # Connect to the SSE endpoint
        async with sse_client(url) as (read_stream, write_stream):
            
            # Establish the JSON-RPC session over the SSE streams
            async with ClientSession(read_stream, write_stream) as session:
                
                # Send the initialize handshake
                await session.initialize()
                print("✅ Connected and initialized session successfully!\n")
                
                # Fetch available tools
                tools = await session.list_tools()
                print(f"Discovered {len(tools.tools)} tools hosted by Fenrir:")
                for tool in tools.tools:
                    print(f" 🛠️  {tool.name}")
                    print(f"    {tool.description}\n")
                    
    except Exception as e:
        print(f"❌ Error connecting to MCP: {e}")
        if "401" in str(e):
            print("\n💡 NOTE: Fenrir returned 401 Unauthorized.")
            print("To test locally without Yggdrasil JWT tokens, make sure AUTH_ENABLED=0 is set in your .env file!")

if __name__ == "__main__":
    asyncio.run(main())
