"""
Example script demonstrating custom tools loaded from JSON config
and merged with MCP tools.
"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from config.custom_tools import get_all_tools
from helper import get_system_prompt


async def main():
    print("=" * 60)
    print("Custom Tools Example")
    print("=" * 60)
    
    # Get all tools (MCP + custom)
    tools = await get_all_tools()
    
    print(f"\nTotal tools loaded: {len(tools)}")
    print("\nTool list:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Create model with tools
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    model_with_tools = model.bind_tools(tools)
    
    # Example: Use a custom tool
    print("\n" + "=" * 60)
    print("Example: Using custom tool 'get_github_repo_info'")
    print("=" * 60)
    
    messages = [
        SystemMessage(content=get_system_prompt(tools)),
        HumanMessage(content="Get information about the langchain-ai/langchain repository on GitHub"),
    ]
    
    response = await model_with_tools.ainvoke(messages)
    messages.append(response)
    
    print(f"\nModel response: {response.content}")
    
    # Handle tool calls
    tool_calls = getattr(response, 'tool_calls', None) or []
    if tool_calls:
        print(f"\nTool calls detected: {len(tool_calls)}")
        
        # Create tool map
        tool_map = {tool.name: tool for tool in tools}
        
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args', {})
                tool_id = tool_call.get('id')
            else:
                tool_name = getattr(tool_call, 'name', None)
                tool_args = getattr(tool_call, 'args', {})
                tool_id = getattr(tool_call, 'id', None)
            
            print(f"\nExecuting: {tool_name}")
            print(f"Arguments: {tool_args}")
            
            if tool_name in tool_map:
                try:
                    tool = tool_map[tool_name]
                    if hasattr(tool, 'ainvoke'):
                        result = await tool.ainvoke(tool_args)
                    else:
                        result = tool.invoke(tool_args)
                    
                    print(f"Result: {result}")
                    
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id
                    ))
                except Exception as e:
                    print(f"Error: {e}")
                    messages.append(ToolMessage(
                        content=f"Error: {str(e)}",
                        tool_call_id=tool_id
                    ))
        
        # Get final response
        final_response = await model_with_tools.ainvoke(messages)
        with open("final_response.md", "w", encoding="utf-8") as f:
            f.write(final_response.content)
        print("\nFinal response written to final_response.md")
    else:
        print("\nNo tool calls made by the model")


if __name__ == "__main__":
    asyncio.run(main())

