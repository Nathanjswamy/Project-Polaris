from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.etl.config import MAX_RETRIES, RETRY_DELAY_SECONDS
from src.etl.utils.logger import get_logger

logger = get_logger(__name__)

def log_attempt_number(retry_state):
    logger.warning(f"Retrying: attempt {retry_state.attempt_number}")

# Production-ready retry decorator for network/API calls
retry_api_call = retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_fixed(RETRY_DELAY_SECONDS),
    retry=retry_if_exception_type(Exception),
    before_sleep=log_attempt_number,
    reraise=True
)
