# Architecture Overview

Understanding how the components of this project work together.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Agent Application                     │
│  (LangChain/LangGraph)                                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ Uses Tools
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│  MCP Tools   │  │ Custom Tools │
│  (server.py) │  │ (JSON config)│
└──────┬───────┘  └──────┬───────┘
       │                 │
       │                 │
       ▼                 ▼
┌─────────────────────────────────┐
│      MCP Server (FastMCP)       │
│  - web_search                   │
│  - http_request                 │
│  - site_search                  │
│  - add, multiply                │
└─────────────────────────────────┘
```

## Component Breakdown

### 1. MCP Server (`server.py`)

**Purpose**: Exposes tools via Model Context Protocol

**Key Components**:
- FastMCP server instance
- Tool definitions with `@mcp.tool()` decorator
- HTTP transport on port 8000

**Tools Exposed**:
- `web_search` - Tavily search integration
- `site_search` - Domain-restricted search
- `http_request` - Generic HTTP client
- `add`, `multiply` - Example math tools

**Transport**: HTTP (streamable_http)

### 2. MCP Client (`config/mcp_client.py`)

**Purpose**: Connects to MCP server and discovers tools

**Key Components**:
- `MultiServerMCPClient` - LangChain MCP adapter
- Connection configuration
- Tool discovery functions

**Functions**:
- `get_tools()` - Get all MCP tools
- `get_tool_by_name()` - Get specific tool

### 3. Custom Tools System (`config/custom_tools.py`)

**Purpose**: Create LangChain tools from JSON configurations

**Key Components**:
- `_make_http_request()` - Client-side HTTP helper
- `create_tool_from_config()` - Tool factory
- `load_custom_tools()` - JSON loader
- `get_all_tools()` - Tool merger

**Flow**:
```
JSON Config → Parse → Create Pydantic Model → Create Function → LangChain Tool
```

### 4. Helper Utilities (`helper.py`)

**Purpose**: Shared utility functions

**Functions**:
- `get_system_prompt()` - Generate system prompt from tools

### 5. Example Applications

#### `langchain_client.py`
- **Purpose**: Basic tool usage example
- **Shows**: Tool discovery, binding, invocation
- **Uses**: MCP tools only

#### `example_custom_tools.py`
- **Purpose**: Custom tools demonstration
- **Shows**: Custom tool loading, merging, usage
- **Uses**: MCP tools + Custom tools

#### `langgraph_app.py`
- **Purpose**: Multi-step workflow example
- **Shows**: State management, node execution
- **Uses**: MCP tools in workflow context

## Data Flow

### Tool Discovery Flow

```
1. Application starts
   ↓
2. MCP Client connects to server
   ↓
3. Client discovers MCP tools
   ↓
4. Custom tools loaded from JSON
   ↓
5. Tools merged into single list
   ↓
6. Tools bound to LLM
```

### Tool Invocation Flow

```
1. LLM decides to use tool
   ↓
2. Tool call extracted from response
   ↓
3. Tool found in tool map
   ↓
4. Tool invoked (MCP or custom)
   ↓
5. Result returned to LLM
   ↓
6. LLM processes result
```

### Custom Tool Execution Flow

```
1. Tool function called with parameters
   ↓
2. Parameters validated (Pydantic)
   ↓
3. URL/headers/body templated
   ↓
4. HTTP request made (client-side)
   ↓
5. Response transformed (JSON/text)
   ↓
6. Result returned
```

## Design Decisions

### Why Client-Side HTTP for Custom Tools?

**Decision**: Custom tools use client-side `requests` library instead of MCP's `http_request` tool.

**Rationale**:
- ✅ Faster (no network round-trip)
- ✅ Simpler (direct function calls)
- ✅ More flexible (easy transformations)
- ✅ Client-specific (custom tools are app-specific)

**Trade-off**: Slight code duplication, but better performance and simplicity.

### Why JSON for Custom Tools?

**Decision**: Use JSON configuration files instead of Python code.

**Rationale**:
- ✅ No code required
- ✅ Easy to version control
- ✅ Simple to edit
- ✅ Can be generated dynamically

**Trade-off**: Less flexible than Python, but sufficient for API tools.

### Why Separate MCP and Custom Tools?

**Decision**: Keep MCP tools and custom tools separate, then merge.

**Rationale**:
- ✅ Clear separation of concerns
- ✅ MCP tools are server-managed
- ✅ Custom tools are client-managed
- ✅ Easy to understand and maintain

**Trade-off**: Slight complexity in merging, but better organization.

## File Dependencies

```
server.py
  └─ config/config.py (env vars)

config/mcp_client.py
  └─ langchain_mcp_adapters

config/custom_tools.py
  └─ config/config.py (timeout)
  └─ langchain_core.tools
  └─ pydantic
  └─ requests

langchain_client.py
  └─ config/mcp_client.py
  └─ helper.py
  └─ langchain_openai
  └─ langchain_core.messages

example_custom_tools.py
  └─ config/custom_tools.py
  └─ helper.py
  └─ langchain_openai

langgraph_app.py
  └─ config/mcp_client.py
  └─ langchain_openai
  └─ langgraph
```

## Configuration Management

### Environment Variables

Loaded via `config/config.py`:
- `TAVILY_API_KEY` - Required for web search
- `OPENAI_API_KEY` - Required for LLM
- `HTTP_TIMEOUT_SECONDS` - Optional (default: 15)

### Tool Configuration

- **MCP Tools**: Defined in `server.py` (Python code)
- **Custom Tools**: Defined in `custom_tools.json` (JSON)

## Extension Points

### Adding New MCP Tools

1. Add function to `server.py`
2. Decorate with `@mcp.tool()`
3. Restart server
4. Tools automatically available

### Adding New Custom Tools

1. Add entry to `custom_tools.json`
2. Tools automatically loaded at runtime
3. No server restart needed

### Creating New Workflows

1. Create new Python file
2. Import tools (MCP or custom)
3. Define workflow with LangGraph
4. Execute workflow

## Security Considerations

### MCP Server
- Runs on localhost by default
- No authentication (local development)
- Tools execute with server permissions

### Custom Tools
- Client-side execution
- No sandboxing
- Uses system's `requests` library
- Validate URLs in production

### API Keys
- Stored in `.env` file
- Never committed to git
- Loaded via `python-dotenv`

## Performance Considerations

### Tool Discovery
- Happens once at startup
- Cached for subsequent calls
- Fast (local HTTP or stdio)

### Tool Invocation
- MCP tools: Network round-trip to server
- Custom tools: Direct function call (faster)
- Both are async-capable

### Workflow Execution
- Nodes execute sequentially by default
- Can be parallelized with LangGraph
- State passed between nodes

## Future Improvements

1. **Tool Caching**: Cache tool results
2. **Rate Limiting**: Add rate limits to tools
3. **Error Recovery**: Better error handling
4. **Tool Versioning**: Version tool definitions
5. **Hot Reload**: Reload custom tools without restart
6. **Tool Testing**: Unit tests for tools
7. **Documentation**: Auto-generate tool docs

