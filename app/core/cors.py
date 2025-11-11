"""
CORS (Cross-Origin Resource Sharing) configuration
"""
from typing import List

# Development CORS settings - allows all origins
# TODO: In production, replace with specific frontend domain(s)
DEV_CORS_ORIGINS = ["*"]

# Production CORS settings - whitelist specific domains
# PROD_CORS_ORIGINS = [
#     "https://yourdomain.com",
#     "https://www.yourdomain.com",
#     "https://app.yourdomain.com"
# ]


def get_cors_origins(debug: bool = True) -> List[str]:
    """
    Get CORS allowed origins based on environment
    
    Args:
        debug: If True, allows all origins (*). If False, uses production whitelist
        
    Returns:
        List of allowed origins
    """
    if debug:
        return DEV_CORS_ORIGINS
    else:
        # TODO: Uncomment and configure production origins
        # return PROD_CORS_ORIGINS
        return DEV_CORS_ORIGINS


# CORS configuration for FastAPI
CORS_CONFIG = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
