# Taqwa Tracker API

A FastAPI microservice for accessing Quranic data including Surahs, Ayahs, and translations.

## Features

- RESTful API for Quranic data
- PostgreSQL database integration
- SQLModel ORM
- Health check endpoints
- Input validation
- Error handling

## Project Structure

```
taqwa-tracker-api/
├── config/
│   └── database.py          # Database configuration
├── entity/
│   └── surah.py            # Database entities
├── model/
│   └── surah.py            # Response models
├── services/
│   └── surah_service.py    # Business logic
├── main.py                 # FastAPI application
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
TAQWA_TRACKER_DB_HOSTNAME=your-db-host
TAQWA_TRACKER_DB_NAME=your-db-name
TAQWA_TRACKER_DB_USERNAME=your-username
TAQWA_TRACKER_DB_PASSWORD=your-password
TAQWA_TRACKER_DB_PORT=5432
```

### Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Checks
- `GET /` - Status check
- `GET /health/db` - Database connection test

### Surah Data
- `GET /surahs/{surah_no}` - Get ayahs for a specific surah (1-114)

## Deployment

### Cloudflare Workers

1. Install Wrangler CLI
2. Set secrets:
```bash
npx wrangler secret put TAQWA_TRACKER_DB_HOSTNAME
npx wrangler secret put TAQWA_TRACKER_DB_NAME
npx wrangler secret put TAQWA_TRACKER_DB_USERNAME
npx wrangler secret put TAQWA_TRACKER_DB_PASSWORD
npx wrangler secret put TAQWA_TRACKER_DB_PORT
```

3. Deploy:
```bash
npx wrangler deploy
```

## Dependencies

- FastAPI - Web framework
- SQLModel - ORM
- Uvicorn - ASGI server
- python-dotenv - Environment variables
- psycopg2-binary - PostgreSQL adapter