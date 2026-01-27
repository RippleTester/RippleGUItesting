import time
from functools import wraps

def timing(func):
    """
    Decorator to measure function execution time in minutes.
    Returns a dict with the result and elapsed time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        elapsed_minutes = (end - start) / 60.0
        return (result, elapsed_minutes)
    return wrapper





