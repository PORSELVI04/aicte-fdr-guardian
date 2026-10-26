from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

from app.models.institution import Institution
from app.models.fdr import FDR
from app.models.document import FDRDocument
from app.models.verification import VerificationReview
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.fdr_action import FDRAction

from app.routers.institutions import router as institutions_router
from app.routers.fdrs import router as fdrs_router
from app.routers.dashboard import router as dashboard_router
from app.routers.documents import router as documents_router
from app.routers.verification import router as verification_router
from app.routers.reviews import router as reviews_router
from app.routers.auth import router as auth_router
from app.routers.notifications import router as notifications_router
from app.routers.audit import router as audit_router
from app.routers.fdr_actions import router as fdr_actions_router
from app.routers.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")

    # Create database tables
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="AICTE FDR Guardian API",
    description="Security Deposit and FDR Management Portal",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(institutions_router)
app.include_router(fdrs_router)
app.include_router(dashboard_router)
app.include_router(documents_router)
app.include_router(verification_router)
app.include_router(reviews_router)
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(audit_router)
app.include_router(fdr_actions_router)
app.include_router(users_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to AICTE FDR Guardian",
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")

    return {
        "status": "healthy",
        "application": "AICTE FDR Guardian",
        "database": "connected",
    }
