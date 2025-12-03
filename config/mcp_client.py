from langchain_mcp_adapters.client import MultiServerMCPClient

# MCP client configuration
# Use stdio transport for local development
# client = MultiServerMCPClient(
#     connections={
#         "mcs-mcp-server": {
#             "transport": "stdio",
#             "command": "python",
#             "args": ["server.py"]
#         }
#     }
# )

# Alternative: Use HTTP transport if server is running separately
client = MultiServerMCPClient(
    connections={
        "mcs-mcp-server": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp"
        }
    }
)


async def get_tools():
    """Get all available tools from the MCP server."""
    return await client.get_tools()


async def get_tool_by_name(name: str):
    """Get a specific tool by name from the MCP server.
    
    Args:
        name: The name of the tool to retrieve
        
    Returns:
        The tool if found, None otherwise
    """
    tools = await get_tools()
    return next((tool for tool in tools if tool.name == name), None)