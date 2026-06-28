from datetime import datetime
from croniter import croniter

def calculate_next_run(cron_expression: str, reference_time: datetime) -> datetime:
    """
    Calculates the next run time for a given cron expression.
    
    Args:
        cron_expression: The cron string (e.g., '0 * * * *')
        reference_time: The time to calculate from (usually utc_now())
        
    Returns:
        A datetime object representing the next run time.
        
    Raises:
        ValueError: If the cron expression is invalid.
    """
    if not croniter.is_valid(cron_expression):
        raise ValueError(f"Invalid cron expression: {cron_expression}")
        
    iterator = croniter(cron_expression, reference_time)
    return iterator.get_next(datetime)
