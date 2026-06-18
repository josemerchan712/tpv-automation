import { apiClient } from './client'

export interface WeeklyReportResponse {
  informe: string
}

export interface StockAnalysisResponse {
  analisis: string
}

export const generateWeeklyReport = (): Promise<WeeklyReportResponse> =>
  apiClient.post<WeeklyReportResponse>('/ai/weekly-report', {})

export const generateStockAnalysis = (): Promise<StockAnalysisResponse> =>
  apiClient.post<StockAnalysisResponse>('/ai/stock-analysis', {})
