import { apiClient } from './client'
import type { CategoryOut } from './categories'

export interface ProductOut {
  id: number
  nombre: string
  precio: string
  stock: number
  stock_minimo: number
  category_id: number | null
  category: CategoryOut | null
}

export interface ProductCreate {
  nombre: string
  precio: string
  stock?: number
  stock_minimo?: number
  category_id?: number | null
}

export interface ProductUpdate {
  nombre?: string
  precio?: string
  stock?: number
  stock_minimo?: number
  category_id?: number | null
}

export const getProducts = (category_id?: number) =>
  apiClient.get<ProductOut[]>(
    category_id != null ? `/products?category_id=${category_id}` : '/products',
  )

export const getProduct = (id: number) => apiClient.get<ProductOut>(`/products/${id}`)

export const createProduct = (data: ProductCreate) =>
  apiClient.post<ProductOut>('/products', data)

export const updateProduct = (id: number, data: ProductUpdate) =>
  apiClient.put<ProductOut>(`/products/${id}`, data)

export const deleteProduct = (id: number) => apiClient.delete(`/products/${id}`)
