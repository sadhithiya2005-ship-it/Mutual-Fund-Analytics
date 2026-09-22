# N100 Financial Intelligence API

## Overview

FastAPI backend for the N100 Financial Intelligence Platform.

The API provides:

- N100 company information
- Financial ratio records
- Company valuation metrics

## Run the API

From the N100 Financial Intelligence Platform directory:

```powershell
python -m uvicorn api.main:app --reload --app-dir src


```markdown
## API Documentation

Swagger UI:

http://127.0.0.1:8000/docs

OpenAPI JSON:

http://127.0.0.1:8000/openapi.json

## Endpoints

### Health

GET `/health`

Returns the API health status.

### Companies

GET `/companies/`

Returns the N100 company list.

Expected company count: **92**

### Financial Ratios

GET `/ratios/{company_id}`

Example:

GET `/ratios/ABB`

Returns financial ratio records for the selected company.

### Valuation

GET `/valuation/{company_id}`

Example:

GET `/valuation/ABB`

Returns valuation metrics for the selected company.

## API Tests

Run:

```powershell
python -m pytest tests/api -v