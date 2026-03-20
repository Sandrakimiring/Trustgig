from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routes import users, jobs, applications, escrow, notifications

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GigPlatform API",
    description="AI-powered freelance marketplace — FastAPI + PostgreSQL + Africa's Talking",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users.router,         prefix="/users",         tags=["Users"])
app.include_router(jobs.router,          prefix="/jobs",          tags=["Jobs"])
app.include_router(applications.router,  prefix="/jobs",          tags=["Applications"])
app.include_router(escrow.router,        prefix="/escrow",        tags=["Escrow"])
app.include_router(notifications.router, prefix="",               tags=["Matching & Notifications"])


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "GigPlatform API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}