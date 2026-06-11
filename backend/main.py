import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import CORS_ORIGINS
from database import init_db
from routers import auth, payments, documents, analyzers, reference, waitlist

# Make app module logs (INFO+) visible alongside uvicorn's own logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Initialize database on startup
init_db()

app = FastAPI(
    title="Can They Fuck Me?",
    description="AI contract analysis: find the clauses designed to screw you before you sign",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
FRONTEND_DIR = (Path(__file__).parent.parent / "frontend" / "dist").resolve()
if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Resolve and confine to the dist directory so crafted paths
        # (e.g. /../backend/.env) cannot escape it.
        file = (FRONTEND_DIR / path).resolve()
        if file.is_file() and file.is_relative_to(FRONTEND_DIR):
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
