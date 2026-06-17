from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/weekly-report")
def weekly_report():
    from fastapi import HTTPException
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/stock-analysis")
def stock_analysis():
    from fastapi import HTTPException
    raise HTTPException(status_code=501, detail="Not implemented yet")
