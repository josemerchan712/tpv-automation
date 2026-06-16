import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchDailyClose } from '../api/reports'

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function fmt(value: string) {
  return parseFloat(value).toFixed(2)
}

export default function DailyCierreWidget() {
  const [fecha, setFecha] = useState(todayStr)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['reports', 'daily-close', fecha],
    queryFn: () => fetchDailyClose(fecha),
  })

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-800">Cierre de Caja</h2>
        <input
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
          aria-label="Fecha del cierre"
          className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {isLoading && <p className="text-gray-400 text-sm">Cargando...</p>}
      {isError && (
        <p className="text-red-500 text-sm">Error al cargar el cierre de caja.</p>
      )}
      {!isLoading && !isError && data && data.num_tickets === 0 && (
        <p className="text-gray-400 text-sm py-4 text-center">
          Sin ventas para esta fecha.
        </p>
      )}
      {!isLoading && !isError && data && data.num_tickets > 0 && (
        <>
          <div className="flex items-end gap-6 mb-4">
            <div>
              <p className="text-3xl font-bold text-gray-900">
                {fmt(data.total_ventas)} €
              </p>
              <p className="text-sm text-gray-500 mt-1">Total ventas</p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-indigo-600">
                {data.num_tickets}
              </p>
              <p className="text-sm text-gray-500 mt-1">Tickets</p>
            </div>
          </div>
          <div className="border-t border-gray-100 pt-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              Desglose por método de pago
            </p>
            <table className="w-full text-sm">
              <tbody>
                {(['efectivo', 'tarjeta', 'bizum', 'otro'] as const).map((method) => (
                  <tr key={method} className="border-b border-gray-50 last:border-0">
                    <td className="py-1.5 capitalize text-gray-700">{method}</td>
                    <td className="py-1.5 text-right font-medium text-gray-900">
                      {fmt(data.desglose_pago[method])} €
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
