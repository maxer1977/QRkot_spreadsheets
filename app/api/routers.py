from fastapi import APIRouter

from app.api.endpoints import (charity_projects_router, donations_router,
                               google_api_router, users_router)

main_router = APIRouter()

main_router.include_router(
    charity_projects_router, prefix="/charity_project", tags=["Charity Project"]
)

main_router.include_router(donations_router, prefix="/donation", tags=["Donations"])

main_router.include_router(google_api_router, prefix="/google", tags=["Google"])

main_router.include_router(users_router)
