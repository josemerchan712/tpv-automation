import { apiClient } from './client'

export interface EmployeeOut {
  id: number
  user_id: number | null
  nombre: string
  puesto: string
  horas_semanales_contratadas: string
  fecha_alta: string
}

export interface EmployeeCreate {
  nombre: string
  puesto: string
  horas_semanales_contratadas: number
  fecha_alta: string
  user_id?: number
}

export interface EmployeeUpdate {
  nombre?: string
  puesto?: string
  horas_semanales_contratadas?: number
  fecha_alta?: string
  user_id?: number
}

export interface HoursSummaryOut {
  employee_id: number
  nombre: string
  periodo: 'semana' | 'mes'
  fecha_inicio: string
  fecha_fin: string
  total_horas_trabajadas: string
  horas_contratadas: string
  diferencia: string
}

export const getEmployees = (): Promise<EmployeeOut[]> =>
  apiClient.get('/employees')

export const getEmployee = (id: number): Promise<EmployeeOut> =>
  apiClient.get(`/employees/${id}`)

export const createEmployee = (data: EmployeeCreate): Promise<EmployeeOut> =>
  apiClient.post('/employees', data)

export const updateEmployee = (id: number, data: EmployeeUpdate): Promise<EmployeeOut> =>
  apiClient.put(`/employees/${id}`, data)

export const deleteEmployee = (id: number): Promise<void> =>
  apiClient.delete(`/employees/${id}`)

export const getHoursSummary = (
  employeeId: number,
  periodo: 'semana' | 'mes',
  fecha: string,
): Promise<HoursSummaryOut> => {
  const qs = new URLSearchParams({ periodo, fecha })
  return apiClient.get(`/employees/${employeeId}/hours-summary?${qs}`)
}
