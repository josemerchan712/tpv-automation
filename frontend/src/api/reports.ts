import { apiClient } from './client'

export interface PaymentBreakdown {
  efectivo: string
  tarjeta: string
  bizum: string
  otro: string
}

export interface DailyCloseOut {
  fecha: string
  total_ventas: string
  num_tickets: number
  desglose_pago: PaymentBreakdown
}

export interface LowStockProductOut {
  id: number
  nombre: string
  stock: number
  stock_minimo: number
}

export interface TopProductOut {
  product_id: number
  nombre: string
  total_cantidad: number
  total_importe: string
}

export const fetchDailyClose = (fecha: string) =>
  apiClient.get<DailyCloseOut>(`/reports/daily-close?fecha=${fecha}`)

export const fetchLowStock = () =>
  apiClient.get<LowStockProductOut[]>('/reports/low-stock')

export const fetchTopProducts = (fechaDesde: string, fechaHasta: string) =>
  apiClient.get<TopProductOut[]>(
    `/reports/top-products?fecha_desde=${fechaDesde}&fecha_hasta=${fechaHasta}`,
  )
