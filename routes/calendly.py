# routes/calendly.py
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
import time
from config.config import get_env

# Import shared token management
from utils.calendly_auth import (
    save_tokens,
    load_tokens,
    delete_tokens,
    get_valid_access_token,
    get_connection_status
)

router = APIRouter(prefix="/calendly", tags=["calendly"])

# Templates
templates = Jinja2Templates(directory="templates")


def get_calendly_credentials():
    """Get Calendly OAuth credentials from environment"""
    client_id = get_env("CALENDLY_CLIENT_ID")
    client_secret = get_env("CALENDLY_CLIENT_SECRET")
    redirect_uri = get_env("CALENDLY_REDIRECT_URI", f"http://localhost:{get_env('FASTAPI_PORT', 8001)}/calendly/auth/callback")
    
    if not client_id or not client_secret:
        raise ValueError("CALENDLY_CLIENT_ID and CALENDLY_CLIENT_SECRET must be set")
    
    return client_id, client_secret, redirect_uri


@router.get("", response_class=HTMLResponse)
async def calendly_connect_page(request: Request):
    """Render the Connect to Calendly page"""
    tokens = load_tokens()
    is_connected = tokens is not None and "access_token" in tokens
    
    return templates.TemplateResponse(
        "calendly/connect.html",
        {
            "request": request,
            "is_connected": is_connected,
        }
    )


@router.get("/auth/start")
async def calendly_auth_start():
    """Start the Calendly OAuth flow - redirects to Calendly authorization page"""
    try:
        client_id, _, redirect_uri = get_calendly_credentials()
    except ValueError as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
    
    oauth_url = (
        f"https://auth.calendly.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
    )
    
    return RedirectResponse(url=oauth_url)


@router.get("/auth/callback")
async def calendly_auth_callback(
    code: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None)
):
    """Handle Calendly OAuth callback - exchange code for tokens"""
    
    # Handle error from Calendly
    if error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": error,
                "error_description": error_description
            }
        )
    
    if not code:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "No authorization code received"
            }
        )
    
    try:
        client_id, client_secret, redirect_uri = get_calendly_credentials()
    except ValueError as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://auth.calendly.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
    
    if response.status_code != 200:
        return JSONResponse(
            status_code=response.status_code,
            content={
                "success": False,
                "error": "Failed to exchange code for tokens",
                "details": response.json()
            }
        )
    
    tokens = response.json()
    
    # Add created_at timestamp for expiry tracking
    tokens["created_at"] = int(time.time())
    
    # Save tokens
    save_tokens(tokens)
    
    # Redirect back to connect page to show success
    return RedirectResponse(url="/calendly?connected=true")


@router.get("/status")
async def calendly_status():
    """Check Calendly connection status with token health"""
    # Get basic connection status
    status = get_connection_status()
    
    if not status["connected"]:
        return status
    
    # Try to get a valid token (will auto-refresh if needed)
    try:
        access_token = get_valid_access_token()
    except RuntimeError as e:
        return {
            "connected": False,
            "error": str(e)
        }
    
    # Verify token by calling Calendly API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.calendly.com/users/me",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
    
    if response.status_code == 200:
        user_data = response.json()
        status["user"] = user_data.get("resource", {}).get("name")
        status["email"] = user_data.get("resource", {}).get("email")
        return status
    else:
        return {
            "connected": False,
            "error": "Token validation failed",
            "status_code": response.status_code
        }


@router.post("/disconnect")
async def calendly_disconnect():
    """Disconnect Calendly (remove stored tokens)"""
    delete_tokens()
    return {"success": True, "message": "Calendly disconnected"}
