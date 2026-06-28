import random

def calculate_backoff(attempt: int, base: int = 2, max_delay: int = 3600) -> float:
    """
    Calculates exponential backoff delay with jitter.
    
    Jitter prevents the "thundering herd" problem where multiple jobs
    failing at the same time all retry at the exact same moment,
    which could overwhelm the target service.
    
    Args:
        attempt: The current retry attempt number (1, 2, 3...)
        base: The backoff multiplier base
        max_delay: The maximum allowed delay in seconds
        
    Returns:
        The total delay in seconds before the next retry.
    """
    # Exponential backoff: base ^ attempt
    delay = min(base ** attempt, max_delay)
    
    # 10% jitter (randomness) added to the delay
    jitter = random.uniform(0, delay * 0.1)
    
    return delay + jitter
