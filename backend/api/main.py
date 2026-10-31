from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.database.session import init_db
from backend.api import (
    auth, users, organizations, discovery, projects, contacts,
    verification, suppression, templates, campaigns, approvals,
    messages, analytics, integrations, audit
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="MailRadar — Developer Outreach Intelligence Platform REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router Registration
v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=v1_prefix)
app.include_router(users.router, prefix=v1_prefix)
app.include_router(organizations.router, prefix=v1_prefix)
app.include_router(discovery.router, prefix=v1_prefix)
app.include_router(projects.router, prefix=v1_prefix)
app.include_router(contacts.router, prefix=v1_prefix)
app.include_router(verification.router, prefix=v1_prefix)
app.include_router(suppression.router, prefix=v1_prefix)
app.include_router(templates.router, prefix=v1_prefix)
app.include_router(campaigns.router, prefix=v1_prefix)
app.include_router(approvals.router, prefix=v1_prefix)
app.include_router(messages.router, prefix=v1_prefix)
app.include_router(analytics.router, prefix=v1_prefix)
app.include_router(integrations.router, prefix=v1_prefix)
app.include_router(audit.router, prefix=v1_prefix)


@app.get("/health", tags=["Health"])
@app.get(f"{v1_prefix}/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "name": "MailRadar API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "online"
    }
