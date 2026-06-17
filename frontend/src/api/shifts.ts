import { apiClient } from './client'

export interface ShiftOut {
  id: number
  employee_id: number
  fecha: string
  hora_inicio: string
  hora_fin: string
  horas_trabajadas: string
}

export interface ShiftCreate {
  employee_id: number
  fecha: string
  hora_inicio: string
  hora_fin: string
}

export interface ShiftUpdate {
  fecha?: string
  hora_inicio?: string
  hora_fin?: string
}

export const getShifts = (params?: {
  employee_id?: number
  fecha_inicio?: string
  fecha_fin?: string
}): Promise<ShiftOut[]> => {
  const qs = new URLSearchParams()
  if (params?.employee_id != null) qs.set('employee_id', String(params.employee_id))
  if (params?.fecha_inicio) qs.set('fecha_inicio', params.fecha_inicio)
  if (params?.fecha_fin) qs.set('fecha_fin', params.fecha_fin)
  const query = qs.toString() ? `?${qs.toString()}` : ''
  return apiClient.get(`/shifts${query}`)
}

export const createShift = (data: ShiftCreate): Promise<ShiftOut> =>
  apiClient.post('/shifts', data)

export const updateShift = (id: number, data: ShiftUpdate): Promise<ShiftOut> =>
  apiClient.put(`/shifts/${id}`, data)

export const deleteShift = (id: number): Promise<void> =>
  apiClient.delete(`/shifts/${id}`)
