# Country Currency & Exchange API

A Django REST Framework API that fetches country data from external APIs, stores it in MySQL, and provides CRUD operations.

## Features

- Fetch country data from REST Countries API
- Get exchange rates from Open Exchange Rates API
- Calculate estimated GDP using population × random(1000–2000) ÷ exchange_rate
- CRUD operations for country data
- Filtering and sorting
- Summary image generation
- Proper error handling with JSON responses

## API Endpoints

- `POST /countries/refresh` - Refresh countries data from external APIs
- `GET /countries` - List all countries (with filtering & sorting)
- `GET /countries/:name` - Get country by name
- `DELETE /countries/:name` - Delete country by name
- `GET /status` - Get API status (total countries & last refresh)
- `GET /countries/image` - Get summary image

## Filtering & Sorting

- Filter by region: `/countries?region=Africa`
- Filter by currency: `/countries?currency=USD`
- Sort by GDP: `/countries?sort=gdp_desc` or `?sort=gdp_asc`
- Sort by population: `/countries?ordering=population` or `?ordering=-population`

## Error Responses

All errors return consistent JSON format:

```json
{"error": "Country not found"}  // 404
{"error": "Validation failed", "details": {...}}  // 400
{"error": "External data source unavailable", "details": "..."}  // 503
{"error": "Internal server error"}  // 500
