from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from config.mcp_client import client
from helper import get_system_prompt


async def main():
    tools = await client.get_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    # Debug: Print tool details
    for tool in tools:
        print(f"Tool: {tool.name}, Description: {getattr(tool, 'description', 'N/A')}")
        print(f"  Type: {type(tool)}, Has ainvoke: {hasattr(tool, 'ainvoke')}, Has invoke: {hasattr(tool, 'invoke')}")
    
    # Create a tool lookup dictionary
    tool_map = {tool.name: tool for tool in tools}

    model = ChatOpenAI(model="gpt-4o", temperature=0)
    # Bind tools with tool_choice to encourage tool use
    model_with_tools = model.bind_tools(tools)
    
    messages = [
        SystemMessage(content=get_system_prompt(tools)),
        HumanMessage(content="Search for the latest AI news articles."),
    ]
    
    # Initial response
    response = await model_with_tools.ainvoke(messages)
    messages.append(response)
    
    print(f"Initial response: {response.content}")
    print(f"Response type: {type(response)}")
    print(f"Response attributes: {dir(response)}")
    
    # Check for tool_calls in various ways
    tool_calls = None
    if hasattr(response, 'tool_calls'):
        tool_calls = response.tool_calls
    elif hasattr(response, 'tool_calls'):
        tool_calls = getattr(response, 'tool_calls', None)
    
    print(f"Tool calls: {tool_calls}")
    if tool_calls:
        print(f"Number of tool calls: {len(tool_calls)}")
        print(f"Tool calls details: {tool_calls}")
    else:
        print("WARNING: No tool calls detected! The model is not invoking tools.")
        print("This might mean:")
        print("1. The model doesn't think it needs to use tools")
        print("2. The tool binding isn't working correctly")
        print("3. The prompt needs to be more explicit")
    
    # Handle tool calls in a loop (in case multiple rounds are needed)
    max_iterations = 5
    iteration = 0
    
    # Get tool_calls from response
    tool_calls = getattr(response, 'tool_calls', None) or []
    
    while tool_calls and iteration < max_iterations:
        iteration += 1
        print(f"\n--- Tool call iteration {iteration} ---")
        
        # Execute each tool call
        for tool_call in tool_calls:
            # Handle both dict and object formats
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name')
                tool_args = tool_call.get('args', {})
                tool_id = tool_call.get('id') or tool_call.get('tool_call_id')
            else:
                # Object format
                tool_name = getattr(tool_call, 'name', None)
                tool_args = getattr(tool_call, 'args', {})
                tool_id = getattr(tool_call, 'id', None) or getattr(tool_call, 'tool_call_id', None)
            
            print(f"Calling tool: {tool_name} with args: {tool_args}")
            
            if tool_name in tool_map:
                try:
                    tool = tool_map[tool_name]
                    # Try async invoke first, fall back to sync
                    if hasattr(tool, 'ainvoke'):
                        tool_result = await tool.ainvoke(tool_args)
                    elif hasattr(tool, 'invoke'):
                        tool_result = tool.invoke(tool_args)
                    else:
                        # Direct call
                        tool_result = tool(tool_args)
                    
                    print(f"Tool result: {tool_result}")
                    
                    # Add tool result message
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_id
                    ))
                except Exception as e:
                    import traceback
                    print(f"Error executing tool {tool_name}: {e}")
                    traceback.print_exc()
                    messages.append(ToolMessage(
                        content=f"Error: {str(e)}",
                        tool_call_id=tool_id
                    ))
            else:
                print(f"Tool {tool_name} not found! Available tools: {list(tool_map.keys())}")
                messages.append(ToolMessage(
                    content=f"Tool {tool_name} not found",
                    tool_call_id=tool_id
                ))
        
        # Get next response from model with tool results
        response = await model_with_tools.ainvoke(messages)
        messages.append(response)
        print(f"\nResponse after tool calls: {response.content}")
        tool_calls = getattr(response, 'tool_calls', None) or []
        print(f"Tool calls: {tool_calls}")
        if tool_calls:
            print(f"Number of tool calls: {len(tool_calls)}")
    
    print(f"\n--- Final Answer ---")
    print(response.content)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())