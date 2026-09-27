from fastapi import APIRouter
from src.api.schemas.common import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
def health():
    """Return API health status."""

    return {
        "status": "healthy"
    }