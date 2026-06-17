import { useAuthStore } from '../store/authStore'
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

export const fetchDailyClose = (fecha: string) => {
  const params = new URLSearchParams({ fecha })
  return apiClient.get<DailyCloseOut>(`/reports/daily-close?${params}`)
}

export const fetchLowStock = () =>
  apiClient.get<LowStockProductOut[]>('/reports/low-stock')

export const fetchTopProducts = (fechaDesde: string, fechaHasta: string) => {
  const params = new URLSearchParams({ fecha_desde: fechaDesde, fecha_hasta: fechaHasta })
  return apiClient.get<TopProductOut[]>(`/reports/top-products?${params}`)
}

export async function downloadRestockCsv(): Promise<void> {
  const token = useAuthStore.getState().token
  const res = await fetch('/api/reports/restock-csv', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (res.status === 401) {
    useAuthStore.getState().logout()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'restock.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
