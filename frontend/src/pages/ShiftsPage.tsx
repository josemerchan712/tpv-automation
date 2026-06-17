import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getEmployees } from '../api/employees'
import { ShiftOut, deleteShift, getShifts } from '../api/shifts'
import ShiftFormModal from '../components/ShiftFormModal'

export default function ShiftsPage() {
  const qc = useQueryClient()
  const today = new Date().toISOString().slice(0, 10)
  const firstOfMonth = today.slice(0, 8) + '01'

  const [fechaInicio, setFechaInicio] = useState(firstOfMonth)
  const [fechaFin, setFechaFin] = useState(today)
  const [filterEmployee, setFilterEmployee] = useState<number | undefined>()
  const [modalShift, setModalShift] = useState<ShiftOut | null | 'new'>(null)

  const { data: employees = [] } = useQuery({ queryKey: ['employees'], queryFn: getEmployees })
  const { data: shifts = [], isLoading, isError } = useQuery({
    queryKey: ['shifts', filterEmployee, fechaInicio, fechaFin],
    queryFn: () => getShifts({ employee_id: filterEmployee, fecha_inicio: fechaInicio, fecha_fin: fechaFin }),
  })

  function invalidate() { qc.invalidateQueries({ queryKey: ['shifts'] }) }

  async function handleDelete(s: ShiftOut) {
    if (!confirm('¿Eliminar este turno?')) return
    await deleteShift(s.id)
    invalidate()
  }

  const empName = (id: number) => employees.find(e => e.id === id)?.nombre ?? `#${id}`

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Turnos</h1>
        <button
          onClick={() => setModalShift('new')}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
        >
          + Nuevo turno
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <select
          className="border rounded-lg px-3 py-2 text-sm"
          value={filterEmployee ?? ''}
          onChange={e => setFilterEmployee(e.target.value ? parseInt(e.target.value) : undefined)}
        >
          <option value="">Todos los empleados</option>
          {employees.map(emp => (
            <option key={emp.id} value={emp.id}>{emp.nombre}</option>
          ))}
        </select>
        <input type="date" className="border rounded-lg px-3 py-2 text-sm"
          value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} />
        <span className="self-center text-slate-400 text-sm">—</span>
        <input type="date" className="border rounded-lg px-3 py-2 text-sm"
          value={fechaFin} onChange={e => setFechaFin(e.target.value)} />
      </div>

      {isError ? (
        <div className="p-4 rounded-xl border border-red-200 bg-red-50">
          <p className="text-red-600 font-medium">No se pudo conectar con el servidor.</p>
          <p className="text-sm text-slate-500 mt-1">Asegúrate de que el backend está en marcha en el puerto 8000.</p>
        </div>
      ) : isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="bg-white rounded-xl border divide-y">
          {shifts.length === 0 && (
            <p className="p-6 text-center text-slate-400">No hay turnos en este período.</p>
          )}
          {shifts.map(s => (
            <div key={s.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium text-slate-800">{empName(s.employee_id)}</p>
                <p className="text-sm text-slate-500">
                  {s.fecha} · {s.hora_inicio.slice(0, 5)}–{s.hora_fin.slice(0, 5)}
                  <span className="ml-2 text-slate-400">({s.horas_trabajadas}h)</span>
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setModalShift(s)}
                  className="px-3 py-1.5 text-xs rounded-lg border hover:bg-slate-50"
                >
                  Editar
                </button>
                <button
                  onClick={() => handleDelete(s)}
                  className="px-3 py-1.5 text-xs rounded-lg border border-red-200 text-red-600 hover:bg-red-50"
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modalShift != null && (
        <ShiftFormModal
          employees={employees}
          shift={modalShift === 'new' ? undefined : modalShift}
          onSaved={invalidate}
          onClose={() => setModalShift(null)}
        />
      )}
    </div>
  )
}
