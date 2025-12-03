import asyncio
from typing import Any, Dict, TypedDict, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from config.mcp_client import get_tool_by_name


class GraphState(TypedDict):
	"""State schema for the LangGraph application."""
	query: Optional[str]
	domain: Optional[str]
	endpoint: Optional[str]
	results: Optional[Any]
	api_response: Optional[Any]
	summary: Optional[Any]


async def build_graph():
	"""Build and return the compiled LangGraph application."""
	# Get tools from MCP server
	web_search = await get_tool_by_name("web_search")
	site_search = await get_tool_by_name("site_search")
	http_tool = await get_tool_by_name("http_request")
	
	# Validate tools were found
	if not web_search:
		raise RuntimeError("web_search tool not found in MCP server")
	if not site_search:
		raise RuntimeError("site_search tool not found in MCP server")
	if not http_tool:
		raise RuntimeError("http_request tool not found in MCP server")

	llm = ChatOpenAI(model="gpt-4o-mini")

	async def planner(state: GraphState) -> Dict[str, Any]:
		"""Plan and execute search based on query and optional domain."""
		query = state.get("query")
		if not query:
			return {"results": None}
		
		if state.get("domain"):
			results = await site_search.ainvoke({
				"query": query,
				"domain": state["domain"],
				"top_k": 3
			})
			return {"results": results}
		else:
			results = await web_search.ainvoke({
				"query": query,
				"top_k": 3
			})
			return {"results": results}

	async def fetch_api(state: GraphState) -> Dict[str, Any]:
		"""Fetch data from an API endpoint if provided."""
		endpoint = state.get("endpoint")
		if endpoint:
			# MCP server expects url first, then method
			resp = await http_tool.ainvoke({
				"url": endpoint,
				"method": "GET",
				"timeout": 15
			})
			return {"api_response": resp}
		return {}

	async def summarize(state: GraphState) -> Dict[str, Any]:
		"""Summarize search results and API response using LLM."""
		messages = [
			{"role": "system", "content": "Summarize the search results and any API response."},
		]
		if state.get("results"):
			messages.append({"role": "user", "content": str(state["results"])})
		if state.get("api_response"):
			messages.append({"role": "user", "content": str(state["api_response"])})
		response = await llm.ainvoke(messages)
		return {"summary": response}

	# Build the graph
	graph = StateGraph(GraphState)
	graph.add_node("plan", planner)
	graph.add_node("api", fetch_api)
	graph.add_node("summarize", summarize)
	graph.add_edge(START, "plan")
	graph.add_edge("plan", "api")
	graph.add_edge("api", "summarize")
	graph.add_edge("summarize", END)
	
	return graph.compile()


async def main():
	"""Main async function to build and run the graph."""
	print("Building graph...")
	app = await build_graph()
	
	print("Graph built. Invoking with test data...")
	result = await app.ainvoke({
		"query": "latest AI news",
		"endpoint": "https://api.github.com"
	})
	
	print("\n=== Result ===")
	print(result.get("summary"))


if __name__ == "__main__":
	asyncio.run(main())
