from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path


class AWSModel(BaseModel):
    access_key_id: str
    secret_access_key: str
    region_name: str
    bucket_name: str


class DatabaseModel(BaseModel):
    user: str
    password: str
    host: str
    port: str
    database: str
    init_command: Optional[str] = None

    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800


class OpenAIModel(BaseModel):
    api_key: str


class SerpapiModel(BaseModel):
    api_key: str
    

class PineconeModel(BaseModel):
    api_key: str
    environment: str
    index_name: str 
    index_name_course_request: str  

class MixpanelModel(BaseModel):
    token: Optional[str] = None
    api_endpoint: str = "https://api.mixpanel.com/track"
    connect_timeout_seconds: float = 2.0
    read_timeout_seconds: float = 2.0
    total_timeout_seconds: float = 3.0
    max_retries: int = 2
    backoff_base_seconds: float = 0.2
    enabled: bool = True

class Settings(BaseSettings):
    db: DatabaseModel
    aws: AWSModel
    openai: OpenAIModel
    pinecone: PineconeModel
    serpapi: SerpapiModel 
    mixpanel: MixpanelModel = MixpanelModel()

    ENVIRONMENT: str  # local | dev | staging | production
    PROJECT_NAME: str = "Insty AI Service"
    API_V1_STR: str = "/api/v1"

    SQS_QUEUE_URL: str
    EXPECTED_TOPIC_ARN: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    internal_api_secret: str = Field(..., alias="INTERNAL_API_SECRET")

    cors_origins_raw: str = Field(..., alias="CORS_ORIGINS")
    base_dir: str = str(Path(__file__).resolve().parent.parent.parent)

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin]

    class Config:
        env_nested_delimiter = '__'
        env_file = ".env"
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings():
    return Settings()


if __name__ == "__main__":
    settings = Settings()
    print(settings.model_dump())
