# app.py - Main FastAPI application
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from config.config import get_env
# Import routes
from routes.calendly import router as calendly_router

# Create FastAPI app
app = FastAPI(
    title="MCS-MCP Web App",
    description="Web interface for MCP server integrations",
    version="0.1.0"
)

# Mount static files (if directory exists)
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(calendly_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root page - simple dashboard/index"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(get_env("FASTAPI_PORT", 8001)), reload=True)
