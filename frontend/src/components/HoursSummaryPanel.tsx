import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { type EmployeeOut, type HoursSummaryOut, getHoursSummary } from '../api/employees'

interface Props {
  employee: EmployeeOut
  onClose: () => void
}

export default function HoursSummaryPanel({ employee, onClose }: Props) {
  const today = new Date().toISOString().slice(0, 10)
  const [periodo, setPeriodo] = useState<'semana' | 'mes'>('semana')
  const [fecha, setFecha] = useState(today)

  const { data, isLoading, error } = useQuery<HoursSummaryOut>({
    queryKey: ['hours-summary', employee.id, periodo, fecha],
    queryFn: () => getHoursSummary(employee.id, periodo, fecha),
  })

  const diferencia = data ? parseFloat(data.diferencia) : null
  const isOver = diferencia !== null && diferencia > 0
  const isUnder = diferencia !== null && diferencia < 0

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">Resumen de horas — {employee.nombre}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">×</button>
        </div>

        <div className="flex gap-3 mb-4">
          <select
            className="border rounded-lg px-3 py-2 text-sm"
            value={periodo}
            onChange={e => setPeriodo(e.target.value as 'semana' | 'mes')}
          >
            <option value="semana">Semana</option>
            <option value="mes">Mes</option>
          </select>
          <input
            type="date"
            className="border rounded-lg px-3 py-2 text-sm"
            value={fecha}
            onChange={e => setFecha(e.target.value)}
          />
        </div>

        {isLoading && <p className="text-slate-500 text-sm">Cargando...</p>}
        {error && <p className="text-red-600 text-sm">Error al cargar el resumen.</p>}

        {data && (
          <div className="space-y-3">
            <div className="text-xs text-slate-400">
              {data.fecha_inicio} — {data.fecha_fin}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-500 mb-1">Horas trabajadas</p>
                <p className="text-2xl font-bold text-slate-800">{data.total_horas_trabajadas}h</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 text-center">
                <p className="text-xs text-slate-500 mb-1">Horas contratadas</p>
                <p className="text-2xl font-bold text-slate-800">{data.horas_contratadas}h</p>
              </div>
            </div>

            <div className={`rounded-lg p-3 text-center ${
              isOver ? 'bg-amber-50 border border-amber-200' :
              isUnder ? 'bg-red-50 border border-red-200' :
              'bg-green-50 border border-green-200'
            }`}>
              <p className={`text-xs font-medium mb-1 ${
                isOver ? 'text-amber-700' : isUnder ? 'text-red-700' : 'text-green-700'
              }`}>
                {isOver ? 'Horas extra' : isUnder ? 'Horas pendientes' : 'Horas completadas'}
              </p>
              <p className={`text-xl font-bold ${
                isOver ? 'text-amber-600' : isUnder ? 'text-red-600' : 'text-green-600'
              }`}>
                {isOver ? '+' : ''}{data.diferencia}h
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
