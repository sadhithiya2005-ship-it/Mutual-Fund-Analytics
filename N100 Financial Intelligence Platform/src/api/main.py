from fastapi import FastAPI

from api.routes.companies import router as companies_router
from api.routes.ratios import router as ratios_router
from api.routes.valuation import router as valuation_router


app = FastAPI(
    title="N100 Financial Intelligence API",
    description="API for the N100 Financial Intelligence Platform",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "N100 Financial Intelligence API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(companies_router)
app.include_router(ratios_router)
app.include_router(valuation_router)