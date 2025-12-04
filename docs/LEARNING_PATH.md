# Learning Path

A step-by-step guide to understanding this project from beginner to advanced.

## 🎯 Project Overview

This project demonstrates how to build AI agents that can use external tools through the Model Context Protocol (MCP) and LangChain. You'll learn:

1. How to create an MCP server
2. How to integrate MCP tools with LangChain
3. How to build custom tools from JSON configurations
4. How to create multi-step workflows with LangGraph

## 📚 Learning Path

### Level 1: Understanding the Basics

**Goal**: Understand what MCP is and how it works

1. **Read**: [README.md](../README.md) - Project overview
2. **Explore**: `server.py` - See how MCP tools are defined
3. **Run**: Start the MCP server
   ```bash
   python server.py
   ```
4. **Learn**: Understand the `@mcp.tool()` decorator and how tools are exposed

**Key Concepts**:
- MCP (Model Context Protocol)
- FastMCP server
- Tool definitions
- HTTP transport

### Level 2: Using MCP Tools

**Goal**: Learn how to use MCP tools in your applications

1. **Read**: `config/mcp_client.py` - See how to connect to MCP server
2. **Explore**: `langchain_client.py` - Simple tool usage example
3. **Run**: 
   ```bash
   # Terminal 1: Start server
   python server.py
   
   # Terminal 2: Run client
   python langchain_client.py
   ```
4. **Understand**: How tools are discovered and invoked

**Key Concepts**:
- MCP client connection
- Tool discovery
- Tool invocation
- LangChain tool binding

### Level 3: Custom Tools

**Goal**: Create your own tools from JSON configurations

1. **Read**: [CUSTOM_TOOLS.md](./CUSTOM_TOOLS.md) - Complete guide
2. **Explore**: `custom_tools.json` - Example configurations
3. **Study**: `config/custom_tools.py` - Implementation details
4. **Run**: 
   ```bash
   python example_custom_tools.py
   ```
5. **Practice**: Create your own tool in `custom_tools.json`

**Key Concepts**:
- JSON-based tool configuration
- Dynamic tool creation
- Parameter templating
- Tool merging

### Level 4: Advanced Workflows

**Goal**: Build multi-step agent workflows

1. **Read**: `langgraph_app.py` - Workflow example
2. **Understand**: State management with TypedDict
3. **Learn**: Node execution and graph flow
4. **Run**:
   ```bash
   python langgraph_app.py
   ```
5. **Experiment**: Modify the workflow to add new steps

**Key Concepts**:
- LangGraph workflows
- State management
- Node execution
- Tool integration in workflows

### Level 5: Building Your Own

**Goal**: Create your own AI agent application

1. **Plan**: Define what your agent should do
2. **Design**: Choose which tools you need
3. **Implement**: Create tools (MCP or custom)
4. **Build**: Create your agent workflow
5. **Test**: Verify everything works

## 🗂️ File Organization

### Core Files (Start Here)

- `README.md` - Project overview and quick start
- `server.py` - MCP server with tool definitions
- `config/mcp_client.py` - MCP client setup

### Examples (Learn By Doing)

- `langchain_client.py` - Basic tool usage (Level 2)
- `example_custom_tools.py` - Custom tools example (Level 3)
- `langgraph_app.py` - Workflow example (Level 4)

### Configuration

- `custom_tools.json` - Custom tool definitions
- `config/custom_tools.py` - Custom tool factory
- `config/config.py` - Environment configuration
- `helper.py` - Shared utilities

### Documentation

- `docs/LEARNING_PATH.md` - This file
- `docs/CUSTOM_TOOLS.md` - Custom tools guide
- `README.md` - Main documentation

## 🎓 Concepts Explained

### MCP (Model Context Protocol)

A standardized protocol for AI applications to access external tools and data. Think of it as a way for AI agents to "call functions" that live outside the AI model.

**Analogy**: Like a restaurant menu - the menu (MCP server) lists available dishes (tools), and you (AI agent) can order any dish (call any tool).

### LangChain Tools

LangChain provides a unified interface for tools. MCP tools are automatically converted to LangChain tools, so you can use them seamlessly.

**Key Point**: Once tools are loaded, they work the same whether they come from MCP or custom JSON configs.

### Custom Tools

Tools defined in JSON that are converted to LangChain tools at runtime. Useful for:
- API integrations
- Reusable endpoints
- No-code tool creation

**When to Use**:
- ✅ Simple API calls
- ✅ Reusable endpoints
- ✅ Quick prototyping
- ❌ Complex logic (use MCP tools instead)

### LangGraph Workflows

Multi-step agent workflows where each step can use tools, make decisions, and pass state to the next step.

**Use Cases**:
- Multi-step research tasks
- Data processing pipelines
- Complex decision-making

## 🛠️ Practice Exercises

### Exercise 1: Add a New MCP Tool

1. Open `server.py`
2. Add a new tool function with `@mcp.tool()` decorator
3. Restart the server
4. Verify it appears in `langchain_client.py`

### Exercise 2: Create a Custom Tool

1. Add a new tool to `custom_tools.json`
2. Use a public API (e.g., weather, news)
3. Test it with `example_custom_tools.py`

### Exercise 3: Build a Simple Workflow

1. Create a new file `my_workflow.py`
2. Define a 2-step workflow:
   - Step 1: Search for information
   - Step 2: Summarize results
3. Use LangGraph to connect the steps

### Exercise 4: Combine MCP and Custom Tools

1. Modify `example_custom_tools.py`
2. Use both MCP tools (web_search) and custom tools
3. Create a workflow that uses both

## 📖 Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [LangChain Documentation](https://python.langchain.com)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph)

## ❓ Common Questions

**Q: Should I use MCP tools or custom tools?**  
A: Use MCP tools for complex logic, custom tools for simple API calls.

**Q: Can I use both together?**  
A: Yes! They're automatically merged when you call `get_all_tools()`.

**Q: Do I need to restart the server for custom tools?**  
A: No, custom tools are loaded at runtime from JSON.

**Q: How do I debug tool issues?**  
A: Check console output, verify JSON syntax, test API endpoints directly.

## 🚀 Next Steps

After completing this learning path:

1. Build your own agent application
2. Contribute improvements to this project
3. Share what you've learned with others
4. Explore more advanced MCP features

Happy learning! 🎉

