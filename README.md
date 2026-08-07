# Project Polaris

Project Polaris is a comprehensive data platform designed to aggregate, process, analyze, and visualize data from various external sources (Google Maps, Reviews, Apify, etc.) into actionable competitive intelligence.

## Architecture
See the detailed system architecture and data pipeline diagrams in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Project Structure
- `backend/`: FastAPI backend powering the API and DB connections.
- `frontend/`: Next.js frontend featuring the Executive Dashboard.
- `database/`: Contains `schema.sql` defining the PostgreSQL data warehouse layers (raw, clean, analytics, features, predictions).
- `src/`: Core Python modules including web scrapers and the ETL pipeline (`src/etl/`).
- `data/`: Local CSV outputs and sample data.

## Getting Started

### 1. Database Setup
You will need a PostgreSQL instance. You can initialize the schemas using:
```bash
psql -U your_user -d your_db -f database/schema.sql
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`. Swagger docs at `/docs`.

### 3. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at `http://localhost:3000`.

## ETL Pipeline
The ETL pipeline is located in `src/etl/`. It is broken down into three stages:
1. `python src/etl/extract.py` - Fetches raw data.
2. `python src/etl/clean.py` - Validates and normalizes data.
3. `python src/etl/load.py` - Computes KPIs and ML features.
