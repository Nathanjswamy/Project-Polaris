# Project Polaris 🚀

## Overview
Production-grade ETL pipeline that processes and enriches data using modular architecture.

## Features
- Extract → Validate → Clean → Normalize → Deduplicate → Enrich → Load
- Robust error handling with retries (Tenacity)
- Data validation using Pydantic
- Database integration using SQLAlchemy

## Tech Stack
- Python
- SQLAlchemy
- Pydantic
- Docker (if used)

## Project Structure
src/etl/
backend/
frontend/

## How to Run
pip install -r requirements.txt
python main.py
