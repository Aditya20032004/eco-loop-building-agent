import asyncio
import sys
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def send_mcp_command(zone_name: str, target_temp: float):
    """
    Spawns the MCP Server as a background subprocess, sends a tool-call request
    over stdio, and returns the result.
    """
    # Configure the client to run our specific server script using the active venv
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.mcp_server"]
    )
    
    try:
        # Establish the stdio pipe
        async with stdio_client(server_params) as (read, write):
            # Open the JSON-RPC session
            async with ClientSession(read, write) as session:
                # Initialize the handshake
                await session.initialize()
                
                # Call the specific tool registered in our FastMCP server
                result = await session.call_tool(
                    "set_zone_temperature", 
                    arguments={
                        "zone_name": zone_name, 
                        "target_temp": target_temp
                    }
                )
                
                # Extract and return the text from the server's response
                return result.content[0].text
                
    except Exception as e:
        print(f"❌ MCP Connection Error: {e}")
        return None

# Quick test execution
if __name__ == "__main__":
    print("Testing MCP Client -> Server Connection...")
    # We will try to set it to 15.0°C. 
    # If the network loop works, the server's tools.py will clamp it to 18.0°C.
    result = asyncio.run(send_mcp_command("Core_bottom", 15.0))
    print(f"MCP Server Response: {result}")