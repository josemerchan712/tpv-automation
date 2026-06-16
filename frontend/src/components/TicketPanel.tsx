import type { ProductOut } from '../api/products'
import type { PaymentMethod } from '../api/sales'

export interface TicketItem {
  product: ProductOut
  cantidad: number
}

const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'tarjeta', label: 'Tarjeta' },
  { value: 'bizum', label: 'Bizum' },
  { value: 'otro', label: 'Otro' },
]

interface Props {
  items: TicketItem[]
  onIncrement: (productId: number) => void
  onDecrement: (productId: number) => void
  onRemove: (productId: number) => void
  paymentMethod: PaymentMethod
  onPaymentChange: (method: PaymentMethod) => void
  onConfirm: () => void
  isSubmitting: boolean
  error: string | null
  successMessage: string | null
}

export default function TicketPanel({
  items,
  onIncrement,
  onDecrement,
  onRemove,
  paymentMethod,
  onPaymentChange,
  onConfirm,
  isSubmitting,
  error,
  successMessage,
}: Props) {
  const total = items.reduce(
    (sum, item) => sum + parseFloat(item.product.precio) * item.cantidad,
    0,
  )

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h2 className="font-bold text-gray-900">Ticket actual</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {items.length === 0 ? (
          <p className="text-center text-gray-400 text-sm py-8">
            Añade productos al ticket
          </p>
        ) : (
          items.map((item) => (
            <div key={item.product.id} className="flex items-center gap-2 text-sm">
              <span className="flex-1 truncate text-gray-800 font-medium">
                {item.product.nombre}
              </span>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => onDecrement(item.product.id)}
                  className="w-6 h-6 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 flex items-center justify-center font-bold"
                  aria-label={`Disminuir ${item.product.nombre}`}
                >
                  −
                </button>
                <span className="w-6 text-center tabular-nums">{item.cantidad}</span>
                <button
                  onClick={() => onIncrement(item.product.id)}
                  disabled={item.cantidad >= item.product.stock}
                  className="w-6 h-6 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 flex items-center justify-center font-bold disabled:opacity-40"
                  aria-label={`Aumentar ${item.product.nombre}`}
                >
                  +
                </button>
              </div>

              <span className="w-16 text-right text-gray-700 tabular-nums shrink-0">
                {(parseFloat(item.product.precio) * item.cantidad).toFixed(2)} €
              </span>

              <button
                onClick={() => onRemove(item.product.id)}
                className="text-gray-300 hover:text-red-400 transition-colors shrink-0"
                aria-label={`Quitar ${item.product.nombre}`}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-gray-100 space-y-3">
        <div className="flex items-center justify-between font-bold text-gray-900 text-lg">
          <span>Total</span>
          <span>{total.toFixed(2)} €</span>
        </div>

        <select
          value={paymentMethod}
          onChange={(e) => onPaymentChange(e.target.value as PaymentMethod)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          aria-label="Método de pago"
        >
          {PAYMENT_METHODS.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
        )}
        {successMessage && (
          <p className="text-sm text-green-700 bg-green-50 rounded-lg px-3 py-2">
            {successMessage}
          </p>
        )}

        <button
          onClick={onConfirm}
          disabled={items.length === 0 || isSubmitting}
          className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Procesando...' : 'Confirmar venta'}
        </button>
      </div>
    </div>
  )
}
