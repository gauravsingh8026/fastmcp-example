# utils/calendly_auth.py
"""
Calendly OAuth Token Management

Handles token storage, expiry checking, and automatic refresh.
Shared between routes/calendly.py and tools/calendly.py
"""

import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config.config import get_env, get_timeout_seconds

# Token storage path
TOKENS_FILE = Path("data/calendly_tokens.json")

# Refresh buffer - refresh token 5 minutes before actual expiry
EXPIRY_BUFFER_SECONDS = 300


def save_tokens(tokens: dict) -> None:
    """Save tokens to file with timestamp"""
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure we have created_at timestamp
    if "created_at" not in tokens:
        tokens["created_at"] = int(time.time())
    
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def load_tokens() -> Optional[Dict[str, Any]]:
    """Load tokens from file"""
    if TOKENS_FILE.exists():
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    return None


def delete_tokens() -> None:
    """Delete stored tokens"""
    if TOKENS_FILE.exists():
        TOKENS_FILE.unlink()


def is_token_expired(tokens: dict) -> bool:
    """
    Check if the access token is expired or about to expire.
    
    Args:
        tokens: Token dictionary with created_at and expires_in
        
    Returns:
        True if token is expired or will expire within buffer period
    """
    if not tokens:
        return True
    
    created_at = tokens.get("created_at")
    expires_in = tokens.get("expires_in")
    
    if not created_at or not expires_in:
        # If we don't have expiry info, assume it might be expired
        # and try to use it (will fail if actually expired)
        return False
    
    # Calculate expiry time
    expiry_time = created_at + expires_in
    current_time = int(time.time())
    
    # Check if expired or will expire within buffer
    return current_time >= (expiry_time - EXPIRY_BUFFER_SECONDS)


def refresh_access_token(tokens: dict) -> Dict[str, Any]:
    """
    Refresh the access token using the refresh token.
    
    Args:
        tokens: Current token dictionary containing refresh_token
        
    Returns:
        New tokens dictionary
        
    Raises:
        RuntimeError: If refresh fails
    """
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("No refresh token available. Please reconnect Calendly.")
    
    client_id = get_env("CALENDLY_CLIENT_ID")
    client_secret = get_env("CALENDLY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise RuntimeError("CALENDLY_CLIENT_ID and CALENDLY_CLIENT_SECRET must be set")
    
    response = requests.post(
        "https://auth.calendly.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        timeout=get_timeout_seconds()
    )
    
    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = error_json.get("error_description", error_json.get("error", response.text))
        except:
            pass
        raise RuntimeError(f"Failed to refresh token: {error_detail}")
    
    new_tokens = response.json()
    
    # Add created_at timestamp
    new_tokens["created_at"] = int(time.time())
    
    # Save the new tokens
    save_tokens(new_tokens)
    
    return new_tokens


def get_valid_access_token() -> str:
    """
    Get a valid access token, refreshing if necessary.
    
    This is the main function to use when you need an access token.
    It handles:
    - Loading tokens from storage
    - Checking if token is expired
    - Automatically refreshing if needed
    
    Returns:
        Valid access token string
        
    Raises:
        RuntimeError: If not connected or refresh fails
    """
    tokens = load_tokens()
    
    if not tokens or "access_token" not in tokens:
        raise RuntimeError(
            "Calendly not connected. Please connect via the web interface first."
        )
    
    # Check if token is expired and refresh if needed
    if is_token_expired(tokens):
        tokens = refresh_access_token(tokens)
    
    return tokens["access_token"]


def get_connection_status() -> Dict[str, Any]:
    """
    Get detailed connection status including token health.
    
    Returns:
        Dictionary with connection status details
    """
    tokens = load_tokens()
    
    if not tokens or "access_token" not in tokens:
        return {
            "connected": False,
            "reason": "No tokens found"
        }
    
    created_at = tokens.get("created_at")
    expires_in = tokens.get("expires_in")
    
    status = {
        "connected": True,
        "has_refresh_token": "refresh_token" in tokens,
    }
    
    if created_at and expires_in:
        expiry_time = created_at + expires_in
        current_time = int(time.time())
        time_remaining = expiry_time - current_time
        
        status["token_expires_at"] = expiry_time
        status["token_expired"] = time_remaining <= 0
        status["seconds_until_expiry"] = max(0, time_remaining)
        status["minutes_until_expiry"] = max(0, time_remaining // 60)
    
    return status
