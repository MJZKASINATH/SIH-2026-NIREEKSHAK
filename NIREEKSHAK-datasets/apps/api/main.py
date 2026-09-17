from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from seed_phase2 import seed_demo_data
from routes import (
    auth,
    projects,
    lifecycle,
    contractors,
    risks,
    analytics,
    investigation,
    audit,
    geostat
)

app = FastAPI(
    title="NIREEKSHAK — AI-Powered MPLADS Risk Intelligence Platform",
    description="Complete end-to-end MPLADS project lifecycle, field verification, entity risk profiling, and explainable fraud anomaly intelligence.",
    version="2.0.0"
)

# Enable CORS for Next.js and frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup lifecycle
@app.on_event("startup")
def on_startup():
    print("Initializing NIREEKSHAK Phase 2 Core...")
    init_db()
    seed_demo_data()
    print("NIREEKSHAK Phase 2 Core Operational.")

# Register sub-routers under /api
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(lifecycle.router, prefix="/api")
app.include_router(contractors.router, prefix="/api")
app.include_router(risks.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(investigation.router, prefix="/api")
app.include_router(investigation.investigation_router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(geostat.router, prefix="/api")

@app.get("/api/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "system": "NIREEKSHAK MPLADS Intelligence Core",
        "version": "2.0.0",
        "phase": "SIH Phase 2 Complete End-to-End"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)