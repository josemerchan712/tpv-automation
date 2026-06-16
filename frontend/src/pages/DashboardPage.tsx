import { useQueryClient } from '@tanstack/react-query'
import DailyCierreWidget from '../components/DailyCierreWidget'
import LowStockWidget from '../components/LowStockWidget'
import TopProductsWidget from '../components/TopProductsWidget'

export default function DashboardPage() {
  const queryClient = useQueryClient()

  function handleRefresh() {
    queryClient.invalidateQueries({ queryKey: ['reports'] })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 text-sm font-medium text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
        >
          Actualizar
        </button>
      </div>

      <DailyCierreWidget />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LowStockWidget />
        <TopProductsWidget />
      </div>
    </div>
  )
}
