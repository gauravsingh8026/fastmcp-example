# MCP Server + LangChain/LangGraph Integration

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io)
[![LangChain](https://img.shields.io/badge/LangChain-Compatible-orange.svg)](https://langchain.com)

> A complete example demonstrating how to build an MCP (Model Context Protocol) server and integrate it with LangChain and LangGraph for building AI agent workflows.

**Keywords:** MCP, Model Context Protocol, LangChain, LangGraph, AI Agents, FastMCP, Tavily, OpenAI, Python, Async, Workflow Automation, Machine Learning, LLM Integration, Agent Framework

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your API keys

# Run the MCP server
python server.py

# In another terminal, run the LangGraph example
python langgraph_app.py
```

## Overview

This project demonstrates a complete integration of **Model Context Protocol (MCP)** with **LangChain** and **LangGraph** for building production-ready AI agent workflows. It provides a working example of how to:

- Create an MCP server that exposes custom tools
- Integrate MCP tools with LangChain agents
- Build multi-step workflows using LangGraph
- Use web search, HTTP requests, and other tools in AI applications

**What is MCP?** The Model Context Protocol is a standardized way for AI applications to access external tools and data sources, enabling more powerful and flexible AI agents.

**Project Components:**
- **MCP Server** (`server.py`) - Exposes tools via the Model Context Protocol over HTTP
- **LangGraph Application** (`langgraph_app.py`) - Demonstrates a multi-step workflow using MCP tools
- **LangChain Client** (`langchain_client.py`) - Shows how to use MCP tools with LangChain agents

## Features

- 🔧 **MCP Server** with multiple tools (web search, HTTP requests, math operations)
- 🔗 **LangGraph Integration** - Multi-step agent workflows
- 🤖 **LangChain Agents** - Tool-using AI agents
- 🔍 **Web Search** - Powered by Tavily API
- 🌐 **HTTP Requests** - Generic HTTP client tool
- ➕ **Math Operations** - Example tools (add, multiply)

## Setup

### 1. Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcs-mcp

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Required for web search functionality
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: HTTP timeout in seconds (default: 15)
HTTP_TIMEOUT_SECONDS=15

# Optional: OpenAI API key (required for LangChain/LangGraph)
OPENAI_API_KEY=your_openai_api_key_here
```

**Getting API Keys:**
- **Tavily API Key**: Sign up at [tavily.com](https://tavily.com) to get a free API key
- **OpenAI API Key**: Get one from [platform.openai.com](https://platform.openai.com)

## Running the MCP Server

The MCP server exposes tools over HTTP transport. It can be run in two ways:

### Option 1: Standalone Server

```bash
python server.py
```

The server will start on `http://localhost:8000` by default. It will:
- Expose all tools via the MCP protocol
- Accept connections from MCP clients
- Handle tool invocations

**Note**: The server runs indefinitely until stopped (Ctrl+C).

### Option 2: Automatic (via Client)

The server is automatically started by the MCP client when using `stdio` transport. However, this project uses HTTP transport, so you need to run the server separately.

## Project Structure

```
mcs-mcp/
├── server.py              # MCP server with tool definitions
├── langgraph_app.py       # LangGraph workflow example
├── langchain_client.py    # LangChain agent example
├── config/
│   ├── config.py          # Environment configuration helpers
│   └── mcp_client.py      # MCP client setup
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## File Purposes

### `server.py` - MCP Server

The MCP server defines and exposes tools that can be used by AI agents. It uses FastMCP to create an HTTP-based MCP server.

**Available Tools:**
- `web_search` - General internet search using Tavily
- `site_search` - Domain-restricted search
- `http_request` - Generic HTTP client for API calls
- `add` - Simple addition tool (example)
- `multiply` - Simple multiplication tool (example)

**Key Features:**
- Tool definitions using `@mcp.tool()` decorator
- Automatic tool discovery via MCP protocol
- HTTP transport for easy integration

**Example:**
```python
@mcp.tool()
def web_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """General internet search via Tavily."""
    # Implementation...
```

### `langgraph_app.py` - LangGraph Workflow

Demonstrates a multi-step agent workflow using LangGraph. The workflow:
1. **Planner** - Executes web search based on query
2. **API Fetcher** - Optionally fetches data from an API endpoint
3. **Summarizer** - Uses LLM to summarize results

**Key Features:**
- State management with TypedDict
- Async node execution
- Tool integration from MCP server
- LLM-powered summarization

**Usage:**
```bash
python langgraph_app.py
```

**Workflow:**
```
START → planner → api → summarize → END
```

The graph processes:
- Input: `{"query": "latest AI news", "endpoint": "https://api.github.com"}`
- Output: Summarized results combining search and API data

### `langchain_client.py` - LangChain Agent

Shows how to use MCP tools with LangChain agents. It demonstrates:
- Tool discovery from MCP server
- Tool binding to LLM
- Tool calling and result handling
- Multi-turn conversations with tool usage

**Key Features:**
- Automatic tool discovery
- Tool invocation handling
- Response processing
- Error handling

**Usage:**
```bash
python langchain_client.py
```

## Adding New Tools

To add a new tool to the MCP server:

1. **Define the tool function** in `server.py`:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> dict:
    """Description of what the tool does."""
    # Your implementation
    return {"result": "value"}
```

2. **No client changes needed!** Tools are automatically discovered via the MCP protocol.

3. **Use in your applications**:

```python
from config.mcp_client import get_tool_by_name

tool = await get_tool_by_name("my_new_tool")
result = await tool.ainvoke({"param1": "value", "param2": 42})
```

## Configuration

### MCP Client Configuration

Edit `config/mcp_client.py` to change transport:

**HTTP Transport (default):**
```python
client = MultiServerMCPClient(
    connections={
        "mcs-mcp-server": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp"
        }
    }
)
```

**Stdio Transport (alternative):**
```python
client = MultiServerMCPClient(
    connections={
        "mcs-mcp-server": {
            "transport": "stdio",
            "command": "python",
            "args": ["server.py"]
        }
    }
)
```

## Examples

### Example 1: Run LangGraph Workflow

```bash
# Terminal 1: Start the MCP server
python server.py

# Terminal 2: Run the LangGraph app
python langgraph_app.py
```

### Example 2: Use Tools Programmatically

```python
import asyncio
from config.mcp_client import get_tool_by_name

async def main():
    # Get a tool
    web_search = await get_tool_by_name("web_search")
    
    # Use the tool
    results = await web_search.ainvoke({
        "query": "Python async programming",
        "top_k": 5
    })
    
    print(results)

asyncio.run(main())
```

### Example 3: Custom LangGraph Node

```python
from config.mcp_client import get_tool_by_name

async def my_custom_node(state: GraphState) -> Dict[str, Any]:
    # Get tool
    tool = await get_tool_by_name("http_request")
    
    # Use tool
    result = await tool.ainvoke({
        "url": "https://api.example.com/data",
        "method": "GET"
    })
    
    return {"custom_data": result}
```

## Troubleshooting

### Server won't start
- Check if port 8000 is available
- Verify all dependencies are installed
- Check `.env` file exists and has required keys

### Tools not found
- Ensure MCP server is running
- Check `config/mcp_client.py` has correct server URL
- Verify tool names match exactly (case-sensitive)

### API Key Errors
- Verify `TAVILY_API_KEY` is set in `.env`
- Check `OPENAI_API_KEY` is set for LLM features
- Ensure `.env` file is in project root

### Import Errors
- Activate virtual environment
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)

## Dependencies

- **fastmcp** - Fast MCP server implementation
- **requests** - HTTP client library
- **tavily-python** - Tavily search API client
- **python-dotenv** - Environment variable management
- **langchain** - LLM application framework
- **langchain-openai** - OpenAI integration
- **langchain-core** - Core LangChain components
- **langgraph** - Graph-based agent workflows
- **langchain-mcp-adapters** - MCP client adapter for LangChain

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary:**
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ✅ No liability
- ✅ No warranty

You are free to use this project for any purpose, including commercial applications. Attribution is appreciated but not required.

## Contributing

Contributions are welcome and greatly appreciated! This project is open to everyone, and we encourage you to help improve it.

### How to Contribute

1. **Fork the Repository**
   - Click the "Fork" button on GitHub to create your own copy

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make Your Changes**
   - Write clean, readable code
   - Follow existing code style and conventions
   - Add comments/docstrings for complex logic
   - Update documentation if needed

4. **Test Your Changes**
   - Ensure existing functionality still works
   - Test new features thoroughly
   - Check for any linting errors

5. **Commit Your Changes**
   ```bash
   git commit -m "Add: description of your changes"
   ```
   Use clear, descriptive commit messages:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for improvements
   - `Docs:` for documentation changes
   - `Refactor:` for code refactoring

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template with:
     - Description of changes
     - Why the changes are needed
     - Any breaking changes
     - Screenshots (if applicable)

### Contribution Guidelines

- **Code Style**: Follow PEP 8 Python style guide
- **Documentation**: Update README.md if adding new features
- **Testing**: Test your changes before submitting
- **Be Respectful**: Be kind and constructive in discussions
- **Ask Questions**: If unsure, open an issue to discuss first

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug Reports**: Found a bug? Open an issue!
- 💡 **Feature Requests**: Have an idea? Share it!
- 📝 **Documentation**: Improve docs, fix typos, add examples
- 🧪 **Testing**: Add tests, improve test coverage
- 🎨 **Code**: Fix bugs, add features, refactor code
- 🌍 **Localization**: Translate documentation
- 📢 **Promotion**: Share the project with others

### Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/yourusername/mcs-mcp/discussions)
- **Found a Bug?** Open a [GitHub Issue](https://github.com/yourusername/mcs-mcp/issues)
- **Security Issue?** Please email directly (don't open a public issue)

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

Thank you for contributing! 🎉
