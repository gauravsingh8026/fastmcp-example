# config/custom_tools.py
"""
Module for loading and creating custom API tools from JSON configuration.
These tools are created as LangChain tools and can be merged with MCP tools.
"""
import json
import os
from typing import Dict, Any, List, Optional, Callable
import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from config.config import get_timeout_seconds


def _make_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Client-side HTTP request helper (similar to MCP's http_request but local).
    Returns status_code, headers, json/text.
    """
    method_upper = (method or "GET").upper()
    to = timeout or get_timeout_seconds()
    
    try:
        resp = requests.request(
            method=method_upper,
            url=url,
            headers=headers or {},
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
    except Exception as e:
        return {
            "status_code": 0,
            "error": str(e),
            "json": None,
            "text": None,
        }


def _format_url(url_template: str, params: Dict[str, Any]) -> str:
    """Format URL template with parameters (e.g., /orders/{order_id})."""
    try:
        return url_template.format(**params)
    except KeyError as e:
        raise ValueError(f"Missing required parameter for URL: {e}")


def _format_headers(headers_template: Dict[str, str], params: Dict[str, Any]) -> Dict[str, str]:
    """Format header templates with parameters."""
    formatted = {}
    for key, value_template in headers_template.items():
        try:
            formatted[key] = value_template.format(**params)
        except KeyError as e:
            raise ValueError(f"Missing required parameter for header '{key}': {e}")
    return formatted


def _format_body(body_template: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """Format body template with parameters."""
    formatted = {}
    for key, value_template in body_template.items():
        if isinstance(value_template, str) and value_template.startswith("{") and value_template.endswith("}"):
            param_name = value_template[1:-1]
            if param_name in params:
                formatted[key] = params[param_name]
            else:
                formatted[key] = value_template  # Keep as-is if param not found
        else:
            formatted[key] = value_template
    return formatted


def create_tool_from_config(tool_config: Dict[str, Any]) -> StructuredTool:
    """
    Create a LangChain StructuredTool from a tool configuration.
    
    Args:
        tool_config: Dictionary containing tool definition
        
    Returns:
        StructuredTool instance ready to use with LangChain
    """
    name = tool_config["name"]
    description = tool_config["description"]
    base_url = tool_config["base_url"]
    method = tool_config.get("method", "GET").upper()
    headers_template = tool_config.get("headers", {})
    body_template = tool_config.get("body_template")
    parameters = tool_config.get("parameters", [])
    response_transform = tool_config.get("response_transform", "json")
    
    # Create Pydantic model for parameters
    # Build annotations and field defaults
    annotations = {}
    field_defaults = {}
    
    for param in parameters:
        param_name = param["name"]
        param_type = param.get("type", "string")
        param_desc = param.get("description", "")
        param_required = param.get("required", False)
        
        # Map JSON types to Python types
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
        }
        python_type = type_mapping.get(param_type, str)
        
        if param_required:
            annotations[param_name] = python_type
            field_defaults[param_name] = Field(description=param_desc)
        else:
            annotations[param_name] = Optional[python_type]
            field_defaults[param_name] = Field(default=None, description=param_desc)
    
    # Create the parameter model class dynamically
    # This approach works with both Pydantic v1 and v2
    model_dict = {"__annotations__": annotations}
    model_dict.update(field_defaults)
    ParamModel = type(f"{name}Params", (BaseModel,), model_dict)
    
    # Create the tool function
    def tool_func(**kwargs) -> Any:
        """Tool function that executes the HTTP request."""
        # Format URL
        url = _format_url(base_url, kwargs)
        
        # Format headers
        headers = _format_headers(headers_template, kwargs) if headers_template else {}
        
        # Prepare body if POST/PUT/PATCH
        json_body = None
        if method in ["POST", "PUT", "PATCH"] and body_template:
            json_body = _format_body(body_template, kwargs)
        
        # Extract query params (params not used in URL/headers/body)
        url_params = {k: v for k, v in kwargs.items() if k not in [p["name"] for p in parameters]}
        
        # Make request
        result = _make_http_request(
            url=url,
            method=method,
            headers=headers,
            params=url_params if url_params else None,
            json_body=json_body,
        )
        
        # Transform response
        if response_transform == "json" and result.get("json"):
            return result["json"]
        elif result.get("text"):
            return result["text"]
        else:
            return result
    
    # Create and return the LangChain tool
    return StructuredTool(
        name=name,
        description=description,
        args_schema=ParamModel,
        func=tool_func,
    )


def load_custom_tools(config_path: str = "custom_tools.json") -> List[StructuredTool]:
    """
    Load custom tools from JSON configuration file.
    
    Args:
        config_path: Path to JSON file containing tool configurations
        
    Returns:
        List of StructuredTool instances
    """
    if not os.path.exists(config_path):
        print(f"Warning: Custom tools config file not found: {config_path}")
        return []
    
    with open(config_path, "r", encoding="utf-8") as f:
        tool_configs = json.load(f)
    
    tools = []
    for config in tool_configs:
        try:
            tool = create_tool_from_config(config)
            tools.append(tool)
            print(f"Loaded custom tool: {tool.name}")
        except Exception as e:
            print(f"Error loading tool '{config.get('name', 'unknown')}': {e}")
            import traceback
            traceback.print_exc()
    
    return tools


async def get_all_tools() -> List[Any]:
    """
    Get all tools: MCP tools + custom tools.
    
    Returns:
        Combined list of all available tools
    """
    from config.mcp_client import get_tools
    
    # Get MCP tools
    mcp_tools = await get_tools()
    
    # Get custom tools
    custom_tools = load_custom_tools()
    
    # Combine and return
    all_tools = list(mcp_tools) + custom_tools
    print(f"Total tools available: {len(all_tools)} ({len(mcp_tools)} MCP + {len(custom_tools)} custom)")
    return all_tools

