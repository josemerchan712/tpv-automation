import { useState } from 'react'
import { generateStockAnalysis } from '../api/ai'

export default function AIStockAnalysisCard() {
  const [analisis, setAnalisis] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate() {
    setIsLoading(true)
    setError(null)
    setAnalisis(null)
    try {
      const data = await generateStockAnalysis()
      setAnalisis(data.analisis)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error desconocido'
      if (msg.includes('GEMINI_API_KEY')) {
        setError('La IA no está configurada en el servidor. Añade GEMINI_API_KEY al archivo .env.')
      } else if (msg.includes('Error al contactar')) {
        setError('No se pudo conectar con la IA. Inténtalo de nuevo en unos minutos.')
      } else {
        setError(`Error al generar el análisis: ${msg}`)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-semibold text-gray-800">Análisis de Stock IA</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Rotación, ajustes de stock mínimo y productos sin movimiento
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="px-3 py-1.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Analizando...' : 'Analizar stock'}
        </button>
      </div>

      {isLoading && (
        <p className="text-gray-400 text-sm text-center py-4">
          La IA está analizando el inventario...
        </p>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {analisis && !isLoading && (
        <div className="mt-2">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed bg-gray-50 rounded-lg p-4 border border-gray-100">
            {analisis}
          </pre>
          <button
            onClick={() => setAnalisis(null)}
            className="mt-2 text-xs text-gray-400 hover:text-gray-600 underline"
          >
            Cerrar análisis
          </button>
        </div>
      )}

      {!analisis && !isLoading && !error && (
        <p className="text-gray-400 text-sm text-center py-4">
          Pulsa el botón para analizar la rotación y estado del inventario.
        </p>
      )}
    </div>
  )
}
