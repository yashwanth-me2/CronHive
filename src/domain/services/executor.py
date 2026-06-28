import time
from typing import Dict, Any, Tuple, Optional
from httpx import AsyncClient, TimeoutException, RequestError
from src.domain.models import ExecutionStatus

async def execute_http_request(
    client: AsyncClient,
    method: str,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout_seconds: int
) -> Tuple[ExecutionStatus, Optional[int], Optional[str], float, Optional[str]]:
    """
    Executes an HTTP request for a job.
    
    This is a pure service function that takes an HTTP client and job details,
    performs the request, and returns the results needed to update the Execution model.
    
    Returns a tuple of:
    (status, http_status_code, response_body_preview, duration_ms, error_message)
    """
    start_time = time.monotonic()
    
    status = ExecutionStatus.FAILED
    http_status_code = None
    response_body_preview = None
    error_message = None
    
    try:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=payload if payload else None,
            timeout=timeout_seconds,
        )
        
        http_status_code = response.status_code
        # Truncate response body to save space (store max 1000 chars)
        response_body_preview = response.text[:1000] if response.text else None
        
        if 200 <= response.status_code < 300:
            status = ExecutionStatus.SUCCESS
        else:
            error_message = f"HTTP request failed with status {response.status_code}"
            
    except TimeoutException:
        error_message = f"Request timed out after {timeout_seconds} seconds"
    except RequestError as e:
        error_message = f"Request failed: {str(e)}"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        
    duration_ms = (time.monotonic() - start_time) * 1000
    
    return status, http_status_code, response_body_preview, duration_ms, error_message
