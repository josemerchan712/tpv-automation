import { apiClient } from './client'

export interface CategoryOut {
  id: number
  nombre: string
}

export const getCategories = () => apiClient.get<CategoryOut[]>('/categories')

export const createCategory = (nombre: string) =>
  apiClient.post<CategoryOut>('/categories', { nombre })

export const updateCategory = (id: number, nombre: string) =>
  apiClient.put<CategoryOut>(`/categories/${id}`, { nombre })

export const deleteCategory = (id: number) => apiClient.delete(`/categories/${id}`)
