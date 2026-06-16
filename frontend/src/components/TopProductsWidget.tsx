import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchTopProducts } from '../api/reports'

function getMonthRange() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const lastDay = new Date(year, now.getMonth() + 1, 0).getDate()
  return {
    desde: `${year}-${month}-01`,
    hasta: `${year}-${month}-${String(lastDay).padStart(2, '0')}`,
  }
}

function fmt(value: string) {
  return parseFloat(value).toFixed(2)
}

export default function TopProductsWidget() {
  const [fechaDesde, setFechaDesde] = useState(() => getMonthRange().desde)
  const [fechaHasta, setFechaHasta] = useState(() => getMonthRange().hasta)

  const { data = [], isLoading, isError } = useQuery({
    queryKey: ['reports', 'top-products', fechaDesde, fechaHasta],
    queryFn: () => fetchTopProducts(fechaDesde, fechaHasta),
  })

  const top10 = data.slice(0, 10)

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="font-semibold text-gray-800">Top Productos</h2>
        <div className="flex items-center gap-2 text-sm">
          <label className="text-gray-500">Desde</label>
          <input
            type="date"
            value={fechaDesde}
            max={fechaHasta}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <label className="text-gray-500">Hasta</label>
          <input
            type="date"
            value={fechaHasta}
            min={fechaDesde}
            onChange={(e) => setFechaHasta(e.target.value)}
            className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
      </div>

      {isLoading && <p className="text-gray-400 text-sm">Cargando...</p>}
      {isError && (
        <p className="text-red-500 text-sm">Error al cargar el ranking de productos.</p>
      )}
      {!isLoading && !isError && top10.length === 0 && (
        <p className="text-gray-400 text-sm py-4 text-center">
          Sin ventas en este período.
        </p>
      )}
      {!isLoading && !isError && top10.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-500 uppercase tracking-wide border-b border-gray-100">
              <th className="pb-2 text-left font-medium">#</th>
              <th className="pb-2 text-left font-medium">Producto</th>
              <th className="pb-2 text-right font-medium">Uds.</th>
              <th className="pb-2 text-right font-medium">Importe</th>
            </tr>
          </thead>
          <tbody>
            {top10.map((product, index) => (
              <tr
                key={product.product_id}
                className="border-b border-gray-50 last:border-0"
              >
                <td className="py-1.5 text-gray-400 font-medium">{index + 1}</td>
                <td className="py-1.5 text-gray-700">{product.nombre}</td>
                <td className="py-1.5 text-right text-gray-900 font-medium">
                  {product.total_cantidad}
                </td>
                <td className="py-1.5 text-right text-gray-900">
                  {fmt(product.total_importe)} €
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
