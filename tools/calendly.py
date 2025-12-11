# tools/calendly.py
"""
Calendly MCP Tools

These tools interact with the Calendly API using stored OAuth tokens.
Tokens are stored by the FastAPI OAuth flow in data/calendly_tokens.json
Token refresh is handled automatically by the shared auth module.
"""

import requests
from typing import Dict, Any, List, Optional
from config.config import get_timeout_seconds

# Import shared token management (handles expiry and auto-refresh)
from utils.calendly_auth import get_valid_access_token

CALENDLY_API_BASE = "https://api.calendly.com"


def _get_current_user_uri() -> str:
    """Get the current user's URI from Calendly"""
    # get_valid_access_token() handles expiry check and auto-refresh
    token = get_valid_access_token()
    response = requests.get(
        f"{CALENDLY_API_BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=get_timeout_seconds()
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Failed to get current user: {response.text}")
    
    return response.json()["resource"]["uri"]


def _calendly_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    json_body: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make an authenticated request to Calendly API"""
    # get_valid_access_token() handles expiry check and auto-refresh
    token = get_valid_access_token()
    
    url = f"{CALENDLY_API_BASE}{endpoint}"
    
    response = requests.request(
        method=method,
        url=url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        params=params,
        json=json_body,
        timeout=get_timeout_seconds()
    )
    
    return {
        "status_code": response.status_code,
        "success": 200 <= response.status_code < 300,
        "data": response.json() if response.text else None
    }


def calendly_list_event_types() -> Dict[str, Any]:
    """
    List all event types for the connected Calendly user.
    
    Returns a list of event types with their URIs, names, durations, and scheduling URLs.
    Use the event_type URI when creating events.
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - event_types: List of event types with uri, name, duration_minutes, scheduling_url
        - error: Error message if failed
    """
    try:
        user_uri = _get_current_user_uri()
        
        result = _calendly_request(
            "GET",
            "/event_types",
            params={"user": user_uri, "active": "true"}
        )
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"API error: {result['data']}"
            }
        
        event_types = []
        for et in result["data"].get("collection", []):
            event_types.append({
                "uri": et.get("uri"),
                "name": et.get("name"),
                "description": et.get("description_plain"),
                "duration_minutes": et.get("duration"),
                "scheduling_url": et.get("scheduling_url"),
                "kind": et.get("kind"),  # solo, group, etc.
            })
        
        return {
            "success": True,
            "event_types": event_types,
            "count": len(event_types)
        }
        
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def calendly_check_availability(
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
    
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - available_slots: List of available time slots with start_time and status
        - error: Error message if failed
    """
    try:
        result = _calendly_request(
            "GET",
            "/event_type_available_times",
            params={
                "event_type": event_type_uri,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"API error: {result['data']}"
            }
        
        available_slots = []
        for slot in result["data"].get("collection", []):
            available_slots.append({
                "start_time": slot.get("start_time"),
                "status": slot.get("status"),  # "available"
                "invitees_remaining": slot.get("invitees_remaining")
            })
        
        return {
            "success": True,
            "available_slots": available_slots,
            "count": len(available_slots)
        }
        
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def calendly_create_event(
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
    
    This books a meeting on behalf of the invitee. Standard Calendly notifications,
    calendar invites, and workflows will run as if booked via the Calendly UI.
    
    NOTE: This endpoint requires a paid Calendly plan (Standard or above).
    
    Args:
        event_type_uri: The URI of the event type to book (from calendly_list_event_types)
        start_time: Start time in ISO 8601 format (e.g., "2025-12-09T14:00:00Z")
        invitee_email: Email address of the person being invited
        invitee_name: Full name of the invitee
        invitee_timezone: Timezone of the invitee (default: "UTC", e.g., "America/New_York")
        location: Optional physical location for in-person meetings
        guests: Optional list of guest email addresses (max 10)
        notes: Optional notes/questions from the invitee
    
    Returns:
        Dictionary containing:
        - success: Whether the event was created successfully
        - event: Event details including uri, start_time, end_time
        - invitee: Invitee details including cancel_url, reschedule_url
        - error: Error message if failed
    """
    try:
        # Build the request body
        body: Dict[str, Any] = {
            "event_type": event_type_uri,
            "start_time": start_time,
            "invitee": {
                "name": invitee_name,
                "email": invitee_email,
                "timezone": invitee_timezone
            }
        }
        
        # Add optional location
        if location:
            body["location"] = {
                "kind": "physical",
                "location": location
            }
        
        # Add optional guests
        if guests:
            body["event_guests"] = guests[:10]  # Max 10 guests
        
        # Add optional notes as Q&A
        if notes:
            body["questions_and_answers"] = [{
                "question": "Additional notes",
                "answer": notes,
                "position": 0
            }]
        
        result = _calendly_request("POST", "/invitees", json_body=body)
        
        if not result["success"]:
            error_data = result.get("data", {})
            error_msg = error_data.get("message", str(error_data))
            
            # Check for common errors
            if result["status_code"] == 403:
                error_msg = "This feature requires a paid Calendly plan (Standard or above)"
            elif result["status_code"] == 400:
                error_msg = f"Invalid request: {error_msg}"
            elif result["status_code"] == 409:
                error_msg = "Time slot is no longer available"
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": result["status_code"]
            }
        
        resource = result["data"].get("resource", {})
        
        return {
            "success": True,
            "invitee": {
                "uri": resource.get("uri"),
                "email": resource.get("email"),
                "name": resource.get("name"),
                "status": resource.get("status"),
                "cancel_url": resource.get("cancel_url"),
                "reschedule_url": resource.get("reschedule_url"),
                "created_at": resource.get("created_at")
            },
            "event_uri": resource.get("event"),
            "message": f"Event created successfully. Invitee {invitee_name} ({invitee_email}) will receive a calendar invite."
        }
        
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
