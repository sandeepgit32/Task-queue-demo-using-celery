import time
import logging
from celery import Celery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)


@app.task(name="tasks.add_together", bind=True, max_retries=3, soft_time_limit=30)
def add_together(self, a, b):
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    try:
        if not all(isinstance(x, (int, float)) for x in [a, b]):
            raise ValueError("Inputs must be numbers")
        time.sleep(10)  # Add 10 second delay
        result = a + b
        logger.info(f"Successfully added {a} + {b} = {result}")
        return result
    except Exception as exc:
        logger.error(f"Error adding numbers: {exc}")
        self.retry(exc=exc, countdown=3)
