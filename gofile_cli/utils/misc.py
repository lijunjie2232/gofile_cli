"""
Miscellaneous Utility Functions

This module provides helper functions for random string generation
and response validation.
"""

import random
import string
from typing import Union

from requests import Response


def random_string(length: int = 8) -> str:
    """
    Generate a random string of lowercase letters and digits.
    
    Args:
        length: Length of the random string. Default: 8.
    
    Returns:
        Random string of specified length.
    
    Example:
        >>> random_string(10)
        'a7b3c9d2e1'
    """
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(length)
    )


async def validate_response(response: Union[Response, any]) -> bool:
    """
    Validate HTTP response status.
    
    Args:
        response: HTTP response object with status attribute.
    
    Returns:
        True if status is 200, 201, or 204; False otherwise.
    
    Example:
        >>> await validate_response(response)
        True
    """
    return response.status in {200, 201, 204}
