from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.schemas.ai import WeeklyReportResponse, StockAnalysisResponse
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/weekly-report", response_model=WeeklyReportResponse)
def weekly_report(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    informe = ai_service.generate_weekly_report(db)
    return WeeklyReportResponse(informe=informe)


@router.post("/stock-analysis", response_model=StockAnalysisResponse)
def stock_analysis(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    analisis = ai_service.generate_stock_analysis(db)
    return StockAnalysisResponse(analisis=analisis)
