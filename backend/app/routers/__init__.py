from fastapi import APIRouter

from . import news, sites


api_router = APIRouter()
api_router.include_router(sites.router)
api_router.include_router(news.router)
