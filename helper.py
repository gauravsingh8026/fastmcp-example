from langchain_core.tools import StructuredTool
from typing import List
def get_system_prompt(tools: List[StructuredTool]) -> str:
    tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
    return f"""You are a helpful assistant with access to the following tools:

    {tool_descriptions}

    CRITICAL INSTRUCTIONS:
    - When the user asks you to use a tool, you MUST actually call it by making a tool call (not just say you will)
    - Tool calls are made automatically when you decide to use a tool - you don't need to describe the action first
    - After a tool is called, you will receive the results automatically
    - Then provide your answer based on the tool results

    Example: If user asks "search for AI news", immediately call the web_search tool with appropriate parameters."""