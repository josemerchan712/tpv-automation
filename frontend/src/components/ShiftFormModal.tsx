import { useState } from 'react'
import { EmployeeOut } from '../api/employees'
import { ShiftCreate, ShiftOut, createShift, updateShift } from '../api/shifts'

interface Props {
  employees: EmployeeOut[]
  shift?: ShiftOut
  onSaved: () => void
  onClose: () => void
}

export default function ShiftFormModal({ employees, shift, onSaved, onClose }: Props) {
  const [employeeId, setEmployeeId] = useState(
    String(shift?.employee_id ?? (employees[0]?.id ?? ''))
  )
  const [fecha, setFecha] = useState(shift?.fecha ?? '')
  const [horaInicio, setHoraInicio] = useState(shift?.hora_inicio?.slice(0, 5) ?? '09:00')
  const [horaFin, setHoraFin] = useState(shift?.hora_fin?.slice(0, 5) ?? '17:00')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (horaFin <= horaInicio) {
      setError('La hora de fin debe ser posterior a la hora de inicio.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (shift) {
        await updateShift(shift.id, {
          fecha,
          hora_inicio: `${horaInicio}:00`,
          hora_fin: `${horaFin}:00`,
        })
      } else {
        const data: ShiftCreate = {
          employee_id: parseInt(employeeId),
          fecha,
          hora_inicio: `${horaInicio}:00`,
          hora_fin: `${horaFin}:00`,
        }
        await createShift(data)
      }
      onSaved()
      onClose()
    } catch {
      setError('Error al guardar el turno.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm">
        <h2 className="text-lg font-bold mb-4">{shift ? 'Editar turno' : 'Nuevo turno'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Empleado</label>
            <select
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={employeeId}
              onChange={e => setEmployeeId(e.target.value)}
              disabled={!!shift}
              required
            >
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Fecha</label>
            <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm"
              value={fecha} onChange={e => setFecha(e.target.value)} required />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">Entrada</label>
              <input type="time" className="w-full border rounded-lg px-3 py-2 text-sm"
                value={horaInicio} onChange={e => setHoraInicio(e.target.value)} required />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">Salida</label>
              <input type="time" className="w-full border rounded-lg px-3 py-2 text-sm"
                value={horaFin} onChange={e => setHoraFin(e.target.value)} required />
            </div>
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border hover:bg-slate-50">
              Cancelar
            </button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50">
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
