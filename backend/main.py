from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import auth, payments, documents, analyzers, reference, waitlist

# Initialize database on startup
init_db()

app = FastAPI(title="Insurance LLM", description="Pixel-powered insurance document intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(documents.router)
app.include_router(analyzers.router)
app.include_router(reference.router)
app.include_router(waitlist.router)


@app.get("/api/health")
async def health():
    return {"message": "cantheyfuckme.com API", "status": "running"}


# Serve built frontend if present (production Docker build)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file = FRONTEND_DIR / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
