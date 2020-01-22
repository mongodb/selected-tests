"""Common models used in selected tests API."""
from pydantic import BaseModel


class CustomResponse(BaseModel):
    custom: str
