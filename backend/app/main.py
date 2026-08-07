from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.api.endpoints import business, insights

# Create DB tables if they don't exist
# In a real production setup, we'd rely strictly on Alembic, but this helps local dev.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Polaris API",
    description="Enterprise API for Cafe Competitive Intelligence",
    version="1.0.0"
)

# Configure CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(business.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Project Polaris API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
