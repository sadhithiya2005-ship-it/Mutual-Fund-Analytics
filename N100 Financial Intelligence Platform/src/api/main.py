
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.companies import router as companies_router
from src.api.routes.documents import router as documents_router
from src.api.routes.health import router as health_router
from src.api.routes.peers import router as peers_router
from src.api.routes.portfolio import router as portfolio_router
from src.api.routes.ratios import router as ratios_router
from src.api.routes.screener import router as screener_router
from src.api.routes.sectors import router as sectors_router

from src.api.routes.valuation import (
    router as valuation_router,
    market_cap_router,
)


# --------------------------------------------------
# Logging configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="N100 Financial Intelligence API",
    description="API for the N100 Financial Intelligence Platform",
    version="1.0.0",
)


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# API prefix
# --------------------------------------------------

API_PREFIX = "/api/v1"


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    """Return API welcome message."""

    return {
        "message": "N100 Financial Intelligence API is running"
    }


# --------------------------------------------------
# Register API routers
# --------------------------------------------------

app.include_router(
    health_router,
    prefix=API_PREFIX,
)

app.include_router(
    companies_router,
    prefix=API_PREFIX,
)

app.include_router(
    ratios_router,
    prefix=API_PREFIX,
)

app.include_router(
    valuation_router,
    prefix=API_PREFIX,
)

# Sprint 6 exact market-cap endpoint
app.include_router(
    market_cap_router,
    prefix=API_PREFIX,
)

app.include_router(
    screener_router,
    prefix=API_PREFIX,
)

app.include_router(
    sectors_router,
    prefix=API_PREFIX,
)

app.include_router(
    peers_router,
    prefix=API_PREFIX,
)

app.include_router(
    portfolio_router,
    prefix=API_PREFIX,
)

app.include_router(
    documents_router,
    prefix=API_PREFIX,
)


# --------------------------------------------------
# Startup log
# --------------------------------------------------

logger.info(
    "N100 Financial Intelligence API initialized"
)