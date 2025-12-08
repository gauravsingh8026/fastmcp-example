from langchain_mcp_adapters.client import MultiServerMCPClient
from config.config import get_env
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
environment = get_env("ENVIRONMENT", "dev")
dev_env_url = f"http://localhost:{get_env('MCP_SERVER_PORT', 8002)}/mcp"
prod_env_url = get_env("MCP_SERVER_URL",dev_env_url)
if environment == "dev":
    url = dev_env_url
else:
    url = prod_env_url
client = MultiServerMCPClient(
    connections={
        "mcs-mcp-server": {
            "transport": "streamable_http",
            "url": url
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