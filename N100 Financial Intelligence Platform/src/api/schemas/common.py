from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str


class CompanyResponse(BaseModel):
    id: Optional[str] = None
    company_name: Optional[str] = None
    website: Optional[str] = None
    face_value: Optional[float] = None
    book_value: Optional[float] = None
    roce_percentage: Optional[float] = None
    roe_percentage: Optional[float] = None


class CompaniesResponse(BaseModel):
    count: int
    companies: list[CompanyResponse]