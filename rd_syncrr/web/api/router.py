from fastapi.routing import APIRouter

from rd_syncrr.web.api import admin, auth, docs, monitoring, sync

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["_auth"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(docs.router)
api_router.include_router(admin.router, prefix="/admin", tags=["_admin"])
