# server.py
from fastmcp import FastMCP
from typing import Optional, Dict, Any, List
import requests
from tavily import TavilyClient
from config.config import get_env, get_timeout_seconds

mcp = FastMCP("mcs-mcp-server")

@mcp.tool(title="add", description="Adds two numbers.")
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool(title="multiply", description="Multiplies two numbers.")
def multiply(a: int, b: int) -> int:
    return a * b

def _get_tavily() -> TavilyClient:
	api_key = get_env("TAVILY_API_KEY")
	if not api_key:
		raise RuntimeError("TAVILY_API_KEY is not set")
	return TavilyClient(api_key=api_key)


@mcp.tool()
def http_request(
	url: str,
	method: str = "GET",
	headers: Optional[Dict[str, str]] = None,
	params: Optional[Dict[str, Any]] = None,
	json_body: Optional[Any] = None,
	timeout: Optional[int] = None,
) -> Dict[str, Any]:
	"""Generic HTTP requester. Returns status_code, headers, json/text."""
	method_upper = (method or "GET").upper()
	to = timeout or get_timeout_seconds()
	resp = requests.request(
		method=method_upper,
		url=url,
		headers=headers,
		params=params,
		json=json_body,
		timeout=to,
	)
	content_type = resp.headers.get("Content-Type", "")
	is_json = "json" in content_type.lower()
	body_json: Optional[Any] = None
	body_text: Optional[str] = None
	if is_json:
		try:
			body_json = resp.json()
		except Exception:
			body_text = resp.text[:100000]
	else:
		body_text = resp.text[:100000]
	return {
		"status_code": resp.status_code,
		"headers": dict(resp.headers),
		"json": body_json,
		"text": body_text,
	}


@mcp.tool()
def web_search(
	query: str,
	top_k: int = 5,
	include_domains: Optional[List[str]] = None,
	exclude_domains: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
	"""General internet search via Tavily. Returns list of {title,url,snippet}."""
	client = _get_tavily()
	resp = client.search(
		query=query,
		max_results=top_k,
		include_domains=include_domains,
		exclude_domains=exclude_domains,
	)
	results = resp.get("results", [])
	trimmed: List[Dict[str, Any]] = []
	for r in results:
		trimmed.append({
			"title": r.get("title"),
			"url": r.get("url"),
			"snippet": r.get("content") or r.get("snippet") or "",
		})
	return trimmed


@mcp.tool()
def site_search(query: str, domain: str, top_k: int = 5) -> List[Dict[str, Any]]:
	"""Domain-restricted search using Tavily include_domains."""
	return web_search(query=query, top_k=top_k, include_domains=[domain])

if __name__ == "__main__":
   mcp.run(transport="http", port=int(get_env("MCP_SERVER_PORT", 8002)))