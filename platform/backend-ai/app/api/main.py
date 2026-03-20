from fastapi import APIRouter, Depends

from app.api.routes import (
    health,
    user_api,
    chatbot_api,
    search_api,
    videos_api,
    community_api,
    course_api
)
from app.api.routes import attach_mixpanel_to_request

api_router = APIRouter(dependencies=[Depends(attach_mixpanel_to_request)])
api_router.include_router(health.router)
api_router.include_router(user_api.router)
api_router.include_router(chatbot_api.router)
api_router.include_router(search_api.router)
api_router.include_router(videos_api.router) 
api_router.include_router(community_api.router)
api_router.include_router(course_api.router)

