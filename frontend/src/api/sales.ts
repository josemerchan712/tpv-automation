import { apiClient } from './client'

export type PaymentMethod = 'efectivo' | 'tarjeta' | 'bizum' | 'otro'

export interface SaleItemCreate {
  product_id: number
  cantidad: number
}

export interface SaleCreate {
  metodo_pago: PaymentMethod
  items: SaleItemCreate[]
}

export interface SaleItemOut {
  id: number
  product_id: number
  cantidad: number
  precio_unitario: string
}

export interface SaleOut {
  id: number
  fecha: string
  total: string
  metodo_pago: PaymentMethod
  user_id: number
  items: SaleItemOut[]
}

export const createSale = (data: SaleCreate) =>
  apiClient.post<SaleOut>('/sales', data)
