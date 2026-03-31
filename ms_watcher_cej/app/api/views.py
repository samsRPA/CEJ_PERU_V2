from fastapi import APIRouter

from app.api.routes import CEJPeruRoutes



apiRouter = APIRouter(prefix="/api/v3")
apiRouter.include_router(CEJPeruRoutes.router,tags=["caseNumber"])

def getApiRouter():
    return apiRouter 