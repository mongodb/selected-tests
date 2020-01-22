"""Controller for the health endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheckResponse(BaseModel):
    online: bool


@router.get("/", response_model=HealthCheckResponse, description="Health check endpoint")
def health() -> HealthCheckResponse:
    """Get the current status of the service."""
    return HealthCheckResponse(online=True)
