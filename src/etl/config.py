import os
from dotenv import load_dotenv

load_dotenv()

# Environment Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://polaris_user:polaris_password@localhost:5432/polaris_db")

# ETL Configuration
ETL_STATE_FILE = os.path.join(os.path.dirname(__file__), "etl_state.json")
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
