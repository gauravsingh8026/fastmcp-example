# server.py
from fastmcp import FastMCP
from typing import Optional, Dict, Any, List
import requests
from tavily import TavilyClient
from config.config import get_env, get_timeout_seconds

# Import Calendly tools
from tools.calendly import (
    calendly_list_event_types,
    calendly_check_availability,
    calendly_create_event
)

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


# ============================================================================
# Calendly Tools
# ============================================================================

@mcp.tool(
    title="calendly_list_event_types",
    description="List all event types for the connected Calendly user. Returns event types with URIs, names, durations, and scheduling URLs. Use the event_type URI when creating events."
)
def mcp_calendly_list_event_types() -> Dict[str, Any]:
    """List all event types for the connected Calendly user."""
    return calendly_list_event_types()


@mcp.tool(
    title="calendly_check_availability",
    description="Check available time slots for a specific Calendly event type within a date range."
)
def mcp_calendly_check_availability(
    event_type_uri: str,
    start_time: str,
    end_time: str
) -> Dict[str, Any]:
    """
    Check available time slots for a specific event type.
    
    Args:
        event_type_uri: The URI of the event type (from calendly_list_event_types)
        start_time: Start of date range in ISO 8601 format (e.g., "2025-12-09T00:00:00Z")
        end_time: End of date range in ISO 8601 format (e.g., "2025-12-10T00:00:00Z")
    """
    return calendly_check_availability(event_type_uri, start_time, end_time)


@mcp.tool(
    title="calendly_create_event",
    description="Create a new Calendly event (book a meeting) on behalf of an invitee. Requires paid Calendly plan."
)
def mcp_calendly_create_event(
    event_type_uri: str,
    start_time: str,
    invitee_email: str,
    invitee_name: str,
    invitee_timezone: str = "UTC",
    location: Optional[str] = None,
    guests: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Calendly event (book a meeting).
    
    Args:
        event_type_uri: The URI of the event type to book
        start_time: Start time in ISO 8601 format (e.g., "2025-12-09T14:00:00Z")
        invitee_email: Email address of the person being invited
        invitee_name: Full name of the invitee
        invitee_timezone: Timezone of the invitee (default: "UTC")
        location: Optional physical location for in-person meetings
        guests: Optional list of guest email addresses (max 10)
        notes: Optional notes from the invitee
    """
    return calendly_create_event(
        event_type_uri=event_type_uri,
        start_time=start_time,
        invitee_email=invitee_email,
        invitee_name=invitee_name,
        invitee_timezone=invitee_timezone,
        location=location,
        guests=guests,
        notes=notes
    )


if __name__ == "__main__":
   mcp.run(transport="http", port=int(get_env("MCP_SERVER_PORT", 8002)))