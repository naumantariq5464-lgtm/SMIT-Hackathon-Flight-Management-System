from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.api_router import api_router
from app.db.init_db import create_all_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    logger.info("Starting up Flight Management System API...")
    try:
        await create_all_tables()
        logger.info("Database tables and seed data initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")
        
    try:
        from app.services.rag_service import rag_service
        logger.info("Initializing RAG knowledge base...")
        rag_service.initialize_knowledge_base()
        logger.info("RAG knowledge base initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize RAG knowledge base: {e}")
        
    yield
    logger.info("Shutting down Flight Management System API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
# Flight Management System API

Enterprise-grade, transactional Flight Management & Booking Backend.

## Key Capabilities
* **Authentication & RBAC**: JWT Bearer authentication with `passenger`, `ops_agent`, and `super_admin` roles.
* **Flight & Inventory Management**: Live capacity breakdown (First, Business, Economy), seat map generation, and safe inventory adjustments.
* **Flight Search**: Real-time seat availability, live dynamic fare options, and multi-class filtering.
* **Holds & Atomicity**: 15-minute price holds, 10-minute seat holds, and row-level locked atomic bookings (`SELECT ... FOR UPDATE`).
* **Idempotency**: Transparent request deduplication and caching for booking endpoints.
* **Cancellations & Refunds**: Policy-based full and partial cancellations with proportional refund and travel credit calculations.
* **Waitlist**: Priority-scored waitlisting by loyalty tier and seat class.
* **Audit Logging**: Immutable audit logging for state-changing operations.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

from app.core.rate_limiter import RateLimitMiddleware

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware (HTTP 429 Protection)
app.add_middleware(RateLimitMiddleware)


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Use jsonable_encoder with custom serializer to safely serialize Pydantic v2 validation errors
    errors = jsonable_encoder(exc.errors(), custom_encoder={Exception: str, ValueError: str})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


# Health Check & Root
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Flight Management System API",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_v1": settings.API_V1_STR,
    }


# Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
