import sys
import json
import logging

# CRITICAL FIX: Force all underlying SDK logs to stderr so they don't corrupt the stdio JSON-RPC pipe
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("❌ Error: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

from src.tools import BuildingTools

# Initialize the MCP server
mcp = FastMCP("EcoLoop Building Control Server")

# Instantiate our existing tools to maintain the safety guardrails
building_tools = BuildingTools()

@mcp.tool()
def set_zone_temperature(zone_name: str, target_temp: float) -> str:
    """
    Adjusts the cooling/heating setpoint for a given building zone.
    The underlying tool automatically clamps values to safe human-comfort bounds (18-30C).
    """
    # Route the MCP network request through our existing native Python tool
    # to guarantee the safety clamp is applied before execution.
    result = building_tools.adjust_setpoint(zone_name, target_temp)
    return result

if __name__ == "__main__":
    # Run the server using stdio transport (standard for local MCP agentic tools)
    print("Starting EcoLoop MCP Server on stdio...", file=sys.stderr)
    mcp.run(transport='stdio')