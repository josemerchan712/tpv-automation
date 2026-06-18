from pydantic import BaseModel


class WeeklyReportResponse(BaseModel):
    informe: str


class StockAnalysisResponse(BaseModel):
    analisis: str
