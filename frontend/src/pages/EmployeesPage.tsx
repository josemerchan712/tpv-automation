import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { EmployeeOut, deleteEmployee, getEmployees } from '../api/employees'
import EmployeeFormModal from '../components/EmployeeFormModal'

export default function EmployeesPage() {
  const qc = useQueryClient()
  const { data: employees = [], isLoading } = useQuery({
    queryKey: ['employees'],
    queryFn: getEmployees,
  })
  const [modalEmployee, setModalEmployee] = useState<EmployeeOut | null | 'new'>(null)

  async function handleDelete(emp: EmployeeOut) {
    if (!confirm(`¿Eliminar a ${emp.nombre}?`)) return
    await deleteEmployee(emp.id)
    qc.invalidateQueries({ queryKey: ['employees'] })
  }

  if (isLoading) return <div className="p-6 text-slate-500">Cargando...</div>

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Empleados</h1>
        <button
          onClick={() => setModalEmployee('new')}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
        >
          + Nuevo empleado
        </button>
      </div>

      <div className="bg-white rounded-xl border divide-y">
        {employees.length === 0 && (
          <p className="p-6 text-center text-slate-400">No hay empleados registrados.</p>
        )}
        {employees.map(emp => (
          <div key={emp.id} className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-slate-800">{emp.nombre}</p>
              <p className="text-sm text-slate-500">
                {emp.puesto} · {emp.horas_semanales_contratadas}h/semana
              </p>
              <p className="text-xs text-slate-400">Alta: {emp.fecha_alta}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setModalEmployee(emp)}
                className="px-3 py-1.5 text-xs rounded-lg border hover:bg-slate-50"
              >
                Editar
              </button>
              <button
                onClick={() => handleDelete(emp)}
                className="px-3 py-1.5 text-xs rounded-lg border border-red-200 text-red-600 hover:bg-red-50"
              >
                Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>

      {modalEmployee != null && (
        <EmployeeFormModal
          employee={modalEmployee === 'new' ? undefined : modalEmployee}
          onSaved={() => qc.invalidateQueries({ queryKey: ['employees'] })}
          onClose={() => setModalEmployee(null)}
        />
      )}
    </div>
  )
}
