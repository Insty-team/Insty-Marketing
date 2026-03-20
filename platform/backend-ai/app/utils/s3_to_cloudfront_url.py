from urllib.parse import urlparse
from app.core.config import get_settings

settings = get_settings()

def convert_s3_to_cloudfront_url(s3_url: str) -> str:
    parsed = urlparse(s3_url)
    key = parsed.path.lstrip("/")

    if settings.ENVIRONMENT == "prod":
        cloudfront_domain = "https://insty.ai.kr"
    else:
        cloudfront_domain = "https://dev.insty.ai.kr"

    return f"{cloudfront_domain}/{key}"
