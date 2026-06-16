import type { ProductOut } from '../api/products'

interface Props {
  product: ProductOut
  isAdmin: boolean
  onEdit: () => void
  onDelete: () => void
}

export default function ProductCard({ product, isAdmin, onEdit, onDelete }: Props) {
  const stockOk = product.stock >= product.stock_minimo

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
      {/* Image placeholder */}
      <div className="aspect-square bg-gray-50 flex items-center justify-center relative">
        <svg
          className="w-12 h-12 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
          />
        </svg>

        {isAdmin && (
          <div className="absolute top-2 right-2 flex gap-1">
            <button
              onClick={onEdit}
              className="p-1.5 bg-white rounded-lg shadow-sm hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 transition-colors"
              title="Editar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
            </button>
            <button
              onClick={onDelete}
              className="p-1.5 bg-white rounded-lg shadow-sm hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
              title="Eliminar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3 flex flex-col gap-1 flex-1">
        <p className="font-semibold text-gray-900 text-sm truncate">{product.nombre}</p>
        {product.category && (
          <span className="inline-block w-fit text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">
            {product.category.nombre}
          </span>
        )}
        <div className="mt-auto pt-2 flex items-center justify-between">
          <span className="text-base font-bold text-gray-900">
            {parseFloat(product.precio).toFixed(2)} €
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              stockOk ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'
            }`}
          >
            {product.stock} uds
          </span>
        </div>
      </div>
    </div>
  )
}
