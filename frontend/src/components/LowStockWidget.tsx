import { useQuery } from '@tanstack/react-query'
import { fetchLowStock, downloadRestockCsv } from '../api/reports'

export default function LowStockWidget() {
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ['reports', 'low-stock'],
    queryFn: fetchLowStock,
  })

  const handleDownload = () => {
    downloadRestockCsv().catch(console.error)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-800">Alertas de Stock</h2>
        <button
          onClick={handleDownload}
          className="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
        >
          Descargar pedido de reposición
        </button>
      </div>

      {isLoading && <p className="text-gray-400 text-sm">Cargando...</p>}
      {isError && (
        <p className="text-red-500 text-sm">Error al cargar alertas de stock.</p>
      )}
      {!isLoading && !isError && data.length === 0 && (
        <p className="text-gray-400 text-sm py-4 text-center">
          Sin alertas — todos los productos tienen stock suficiente.
        </p>
      )}
      {!isLoading && !isError && data.length > 0 && (
        <ul className="space-y-2">
          {data.map((product) => (
            <li
              key={product.id}
              className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0"
            >
              <span className="text-sm text-gray-700">{product.nombre}</span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">
                  {product.stock}/{product.stock_minimo}
                </span>
                {product.stock === 0 && (
                  <span className="text-xs bg-red-100 text-red-700 rounded px-1.5 py-0.5 font-medium">
                    Sin stock
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
