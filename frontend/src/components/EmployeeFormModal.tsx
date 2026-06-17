import { useState } from 'react'
import { EmployeeCreate, EmployeeOut, createEmployee, updateEmployee } from '../api/employees'

interface Props {
  employee?: EmployeeOut
  onSaved: () => void
  onClose: () => void
}

export default function EmployeeFormModal({ employee, onSaved, onClose }: Props) {
  const [nombre, setNombre] = useState(employee?.nombre ?? '')
  const [puesto, setPuesto] = useState(employee?.puesto ?? '')
  const [horas, setHoras] = useState(employee?.horas_semanales_contratadas ?? '40')
  const [fechaAlta, setFechaAlta] = useState(employee?.fecha_alta ?? '')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const data: EmployeeCreate = {
        nombre: nombre.trim(),
        puesto: puesto.trim(),
        horas_semanales_contratadas: parseFloat(horas),
        fecha_alta: fechaAlta,
      }
      if (employee) {
        await updateEmployee(employee.id, data)
      } else {
        await createEmployee(data)
      }
      onSaved()
      onClose()
    } catch {
      setError('Error al guardar el empleado.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">
          {employee ? 'Editar empleado' : 'Nuevo empleado'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Nombre</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={nombre}
              onChange={e => setNombre(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Puesto</label>
            <input
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={puesto}
              onChange={e => setPuesto(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Horas semanales contratadas</label>
            <input
              type="number"
              min="0"
              max="168"
              step="0.5"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={horas}
              onChange={e => setHoras(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Fecha de alta</label>
            <input
              type="date"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={fechaAlta}
              onChange={e => setFechaAlta(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
