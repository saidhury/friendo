import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import user, task, energy
from config import get_settings

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Smart Companion API",
    description="Neuro-Inclusive Energy-Adaptive Micro-Wins System",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(task.router)
app.include_router(energy.router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()
    print(f"🚀 {settings.APP_NAME} started!")
    print("📦 Database initialized")

# Serve static files (frontend build)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    @app.get("/")
    async def serve_root():
        """Serve the frontend application."""
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA for all other routes."""
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
