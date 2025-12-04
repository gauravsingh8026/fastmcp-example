# Custom Tools Guide

Learn how to create and use custom API tools from JSON configuration files.

## Overview

Custom tools allow you to define reusable API endpoints as LangChain tools without writing Python code. Simply define your API configuration in JSON, and the system automatically creates LangChain tools that can be used by AI agents.

## Why Custom Tools?

- **No Code Required**: Define tools using simple JSON configuration
- **Dynamic Loading**: Tools are loaded at runtime from JSON files
- **Type Safety**: Automatic parameter validation using Pydantic
- **Template Support**: Use `{parameter}` placeholders in URLs, headers, and bodies
- **Merged with MCP Tools**: Custom tools work seamlessly alongside MCP server tools

## Quick Start

1. **Create a tool configuration** in `custom_tools.json`:

```json
{
  "name": "get_order_details",
  "description": "Fetches order details from ecommerce API by order ID",
  "base_url": "https://api.ecommerce.com/orders/{order_id}",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {api_token}",
    "Content-Type": "application/json"
  },
  "parameters": [
    {
      "name": "order_id",
      "type": "string",
      "required": true,
      "description": "The unique identifier of the order"
    },
    {
      "name": "api_token",
      "type": "string",
      "required": true,
      "description": "API authentication token"
    }
  ],
  "response_transform": "json"
}
```

2. **Load and use the tools**:

```python
from config.custom_tools import get_all_tools

# Get all tools (MCP + custom)
tools = await get_all_tools()

# Bind to LLM
model_with_tools = model.bind_tools(tools)
```

3. **Run the example**:

```bash
python example_custom_tools.py
```

## Tool Configuration Schema

### Required Fields

- `name` (string): Unique tool name (used as function name)
- `description` (string): Tool description (shown to LLM)
- `base_url` (string): API endpoint URL with optional `{parameter}` placeholders
- `method` (string): HTTP method (GET, POST, PUT, DELETE, PATCH)

### Optional Fields

- `headers` (object): HTTP headers with optional `{parameter}` placeholders
- `body_template` (object): Request body template for POST/PUT/PATCH requests
- `parameters` (array): Parameter definitions
- `response_transform` (string): How to process response ("json" or "text", default: "json")

### Parameter Definition

Each parameter in the `parameters` array should have:

- `name` (string): Parameter name
- `type` (string): Parameter type - "string", "number", "integer", "boolean"
- `required` (boolean): Whether parameter is required
- `description` (string): Parameter description (shown to LLM)

## Examples

### Example 1: GET Request with Path Parameter

```json
{
  "name": "get_user_profile",
  "description": "Fetches user profile by user ID",
  "base_url": "https://api.example.com/users/{user_id}",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {api_token}"
  },
  "parameters": [
    {
      "name": "user_id",
      "type": "string",
      "required": true,
      "description": "User ID"
    },
    {
      "name": "api_token",
      "type": "string",
      "required": true,
      "description": "API authentication token"
    }
  ]
}
```

### Example 2: POST Request with JSON Body

```json
{
  "name": "create_product",
  "description": "Creates a new product",
  "base_url": "https://api.ecommerce.com/products",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer {api_token}",
    "Content-Type": "application/json"
  },
  "parameters": [
    {
      "name": "name",
      "type": "string",
      "required": true,
      "description": "Product name"
    },
    {
      "name": "price",
      "type": "number",
      "required": true,
      "description": "Product price"
    },
    {
      "name": "api_token",
      "type": "string",
      "required": true,
      "description": "API token"
    }
  ],
  "body_template": {
    "name": "{name}",
    "price": "{price}"
  }
}
```

### Example 3: Public API (No Auth)

```json
{
  "name": "get_github_repo_info",
  "description": "Fetches GitHub repository information",
  "base_url": "https://api.github.com/repos/{owner}/{repo}",
  "method": "GET",
  "headers": {
    "Accept": "application/vnd.github.v3+json"
  },
  "parameters": [
    {
      "name": "owner",
      "type": "string",
      "required": true,
      "description": "Repository owner"
    },
    {
      "name": "repo",
      "type": "string",
      "required": true,
      "description": "Repository name"
    }
  ]
}
```

## How It Works

1. **Configuration Loading**: `load_custom_tools()` reads JSON file and parses tool definitions
2. **Tool Creation**: `create_tool_from_config()` converts each config into a LangChain `StructuredTool`:
   - Creates dynamic Pydantic model for parameter validation
   - Generates function that executes HTTP request
   - Handles URL/header/body templating
3. **Tool Merging**: `get_all_tools()` combines MCP tools + custom tools
4. **LLM Integration**: All tools are bound to the LLM and can be called automatically

## Architecture Decision: Client-Side HTTP

Custom tools use **client-side HTTP requests** (not MCP's `http_request` tool) because:

✅ **Faster**: No network round-trip to MCP server  
✅ **Simpler**: Direct function calls  
✅ **More Flexible**: Easy to add transformations  
✅ **Client-Specific**: Custom tools are application-specific  

MCP's `http_request` is better for:
- Shared tools across multiple clients
- Centralized tool management
- Server-side rate limiting/security

## File Structure

```
mcs-mcp/
├── custom_tools.json          # Tool configurations
├── config/
│   └── custom_tools.py        # Tool factory and loader
├── example_custom_tools.py    # Example usage
└── helper.py                  # Shared utilities
```

## Advanced Usage

### Custom Response Transformation

The `response_transform` field controls how responses are processed:

- `"json"`: Returns parsed JSON (default)
- `"text"`: Returns raw text response
- If JSON parsing fails, falls back to text

### Error Handling

Tools automatically handle:
- Missing required parameters
- HTTP errors (returns error in response)
- JSON parsing failures (falls back to text)
- Network timeouts (uses `HTTP_TIMEOUT_SECONDS` from config)

### Multiple Tools in One File

You can define multiple tools in `custom_tools.json` as an array:

```json
[
  {
    "name": "tool1",
    ...
  },
  {
    "name": "tool2",
    ...
  }
]
```

## Troubleshooting

### Tool Not Loading

- Check JSON syntax is valid
- Verify all required fields are present
- Check console for error messages

### Parameter Errors

- Ensure parameter names match placeholders in URL/headers/body
- Verify required parameters are provided
- Check parameter types match expected values

### HTTP Errors

- Verify API endpoint URL is correct
- Check authentication tokens are valid
- Ensure HTTP method matches API expectations

## Next Steps

- See `example_custom_tools.py` for complete working example
- Check `config/custom_tools.py` for implementation details
- Review `custom_tools.json` for more examples

