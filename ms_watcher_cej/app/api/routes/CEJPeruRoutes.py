from typing import Optional
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from app.dependencies.Dependencies import Dependencies
from app.domain.interfaces.ICEJPeruService import ICEJPeruService

router = APIRouter(
    prefix = "/radicadosCEJ"
)

@router.post(
    "/{caseNumber}/publish",
    status_code = status.HTTP_202_ACCEPTED
)
@inject
async def publishCaseNumber(
    caseNumber:str,
    cejPeruService: ICEJPeruService = Depends(Provide[Dependencies.cejPeruService])
):
    try:
  
        await cejPeruService.publishCaseNumber(caseNumber)
        responseData = {"message": f"Request accepted for processing. Case number : {caseNumber}  has been queued."}
        return responseData
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException( status_code=500, detail="Internal server error")

#All
@router.post(
    "/all",
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def publish_all_notifications(
 cejPeruService: ICEJPeruService = Depends(Provide[Dependencies.cejPeruService])
):
    try:
        await cejPeruService.publishAllCaseNumbers()
        responseData = { "message": f"Background publishing task started"}
        return responseData
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException( status_code=500, detail="Internal server error")
    