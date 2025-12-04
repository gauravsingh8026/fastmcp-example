# Quick Reference

Quick lookup guide for common tasks and patterns.

## Common Tasks

### Start MCP Server

```bash
python server.py
```

Server runs on `http://localhost:8000` by default.

### Get All Tools (MCP + Custom)

```python
from config.custom_tools import get_all_tools

tools = await get_all_tools()
```

### Get Only MCP Tools

```python
from config.mcp_client import get_tools

tools = await get_tools()
```

### Get Specific Tool

```python
from config.mcp_client import get_tool_by_name

tool = await get_tool_by_name("web_search")
result = await tool.ainvoke({"query": "AI news", "top_k": 5})
```

### Bind Tools to LLM

```python
from langchain_openai import ChatOpenAI
from config.custom_tools import get_all_tools

tools = await get_all_tools()
model = ChatOpenAI(model="gpt-4o")
model_with_tools = model.bind_tools(tools)
```

### Create System Prompt

```python
from helper import get_system_prompt
from config.custom_tools import get_all_tools

tools = await get_all_tools()
prompt = get_system_prompt(tools)
```

## Tool Configuration Patterns

### GET Request with Path Parameter

```json
{
  "name": "get_item",
  "description": "Get item by ID",
  "base_url": "https://api.example.com/items/{item_id}",
  "method": "GET",
  "parameters": [
    {"name": "item_id", "type": "string", "required": true}
  ]
}
```

### POST Request with Body

```json
{
  "name": "create_item",
  "description": "Create new item",
  "base_url": "https://api.example.com/items",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "parameters": [
    {"name": "name", "type": "string", "required": true}
  ],
  "body_template": {
    "name": "{name}"
  }
}
```

### Request with Authentication

```json
{
  "name": "authenticated_request",
  "description": "Authenticated API call",
  "base_url": "https://api.example.com/data",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {api_token}"
  },
  "parameters": [
    {"name": "api_token", "type": "string", "required": true}
  ]
}
```

## Common Patterns

### Tool Invocation Loop

```python
tool_calls = getattr(response, 'tool_calls', None) or []
tool_map = {tool.name: tool for tool in tools}

for tool_call in tool_calls:
    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name')
    tool_args = tool_call.get('args', {}) if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
    tool_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id')
    
    if tool_name in tool_map:
        tool = tool_map[tool_name]
        result = await tool.ainvoke(tool_args) if hasattr(tool, 'ainvoke') else tool.invoke(tool_args)
        messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))
```

### Error Handling

```python
try:
    result = await tool.ainvoke(args)
except Exception as e:
    error_msg = f"Error: {str(e)}"
    messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id))
```

## File Locations

| What | Where |
|------|-------|
| MCP Server | `server.py` |
| MCP Client Config | `config/mcp_client.py` |
| Custom Tools Config | `custom_tools.json` |
| Custom Tools Code | `config/custom_tools.py` |
| Environment Config | `config/config.py` |
| Helper Functions | `helper.py` |

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `TAVILY_API_KEY` | Yes | - | Web search API |
| `OPENAI_API_KEY` | Yes | - | LLM API |
| `HTTP_TIMEOUT_SECONDS` | No | 15 | HTTP timeout |

## Tool Types

| Type | Location | When to Use |
|------|----------|-------------|
| MCP Tools | `server.py` | Complex logic, server-managed |
| Custom Tools | `custom_tools.json` | Simple API calls, client-specific |

## Common Issues

### Tool Not Found
- Check tool name spelling (case-sensitive)
- Verify server is running
- Check tool is registered

### Import Errors
- Activate virtual environment
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)

### API Key Errors
- Verify `.env` file exists
- Check key is set correctly
- Restart server after changing `.env`

## Examples by Use Case

### Web Search
```python
tool = await get_tool_by_name("web_search")
results = await tool.ainvoke({"query": "Python async", "top_k": 5})
```

### HTTP Request
```python
tool = await get_tool_by_name("http_request")
result = await tool.ainvoke({
    "url": "https://api.example.com/data",
    "method": "GET"
})
```

### Custom Tool
```python
tools = await get_all_tools()
# Custom tool is automatically available
# LLM will use it when appropriate
```

## Next Steps

- See [LEARNING_PATH.md](./LEARNING_PATH.md) for step-by-step guide
- See [CUSTOM_TOOLS.md](./CUSTOM_TOOLS.md) for custom tools guide
- See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design

