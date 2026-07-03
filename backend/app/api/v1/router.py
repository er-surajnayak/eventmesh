"""Aggregate router for API v1.

Each domain module contributes its own router; this file is the single place
they are mounted. Routers are added as their phases land.
"""

from fastapi import APIRouter

from app.modules.organizers.router import router as organizers_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(organizers_router)

# Mounted in later phases:
#   events        (Phase 3)
#   sync/admin    (Phase 4)
#   search        (Phase 5)
