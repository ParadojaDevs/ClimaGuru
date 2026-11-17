"""Async ingestion tasks with retries and rate limiting."""
import logging
import time
from typing import Dict, Any, Callable
try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except Exception:
    retry = stop_after_attempt = wait_exponential = None

logger = logging.getLogger(__name__)


class TokenBucket:
    def __init__(self, rate_per_sec=1.0, capacity=10):
        self.rate = rate_per_sec
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.time()

    def consume(self, tokens=1.0):
        now = time.time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


def with_rate_limit(bucket: TokenBucket):
    def deco(f):
        def w(*a, **k):
            while not bucket.consume():
                time.sleep(0.1)
            return f(*a, **k)
        return w
    return deco


def run_ingestion_with_retry(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    if retry:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5))
        def _run():
            return func(*args, **kwargs)
        try:
            return _run()
        except Exception as e:
            logger.error(f"Task failed after retries: {e}")
            return {'status':'error','error':str(e)}
    else:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {'status':'error','error':str(e)}
