import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getCategories } from '../api/categories'
import { getProducts } from '../api/products'
import type { ProductOut } from '../api/products'
import { createSale } from '../api/sales'
import type { PaymentMethod } from '../api/sales'
import ProductCard from '../components/ProductCard'
import TicketPanel from '../components/TicketPanel'
import type { TicketItem } from '../components/TicketPanel'

export default function SalesPage() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [ticketItems, setTicketItems] = useState<TicketItem[]>([])
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('efectivo')
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const successTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const queryClient = useQueryClient()

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const {
    data: products = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['products', categoryFilter],
    queryFn: () => getProducts(categoryFilter ? Number(categoryFilter) : undefined),
  })

  const saleMutation = useMutation({
    mutationFn: createSale,
    onSuccess: () => {
      setTicketItems([])
      setError(null)
      setSuccessMessage('Venta registrada correctamente')
      queryClient.invalidateQueries({ queryKey: ['products'] })
      if (successTimerRef.current) clearTimeout(successTimerRef.current)
      successTimerRef.current = setTimeout(() => setSuccessMessage(null), 3000)
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : 'Error al registrar la venta'
      setError(message)
    },
  })

  useEffect(() => {
    return () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current)
    }
  }, [])

  const filtered = products.filter((p) =>
    p.nombre.toLowerCase().includes(search.toLowerCase()),
  )

  function handleAddToTicket(product: ProductOut) {
    setError(null)
    setTicketItems((prev) => {
      const existing = prev.find((i) => i.product.id === product.id)
      if (existing) {
        if (existing.cantidad >= product.stock) return prev
        return prev.map((i) =>
          i.product.id === product.id ? { ...i, cantidad: i.cantidad + 1 } : i,
        )
      }
      return [...prev, { product, cantidad: 1 }]
    })
  }

  function handleIncrement(productId: number) {
    setError(null)
    setTicketItems((prev) =>
      prev.map((i) => {
        if (i.product.id !== productId) return i
        if (i.cantidad >= i.product.stock) return i
        return { ...i, cantidad: i.cantidad + 1 }
      }),
    )
  }

  function handleDecrement(productId: number) {
    setError(null)
    setTicketItems((prev) =>
      prev
        .map((i) =>
          i.product.id === productId ? { ...i, cantidad: i.cantidad - 1 } : i,
        )
        .filter((i) => i.cantidad > 0),
    )
  }

  function handleRemove(productId: number) {
    setError(null)
    setTicketItems((prev) => prev.filter((i) => i.product.id !== productId))
  }

  function handleConfirm() {
    if (saleMutation.isPending || ticketItems.length === 0) return
    setError(null)
    saleMutation.mutate({
      metodo_pago: paymentMethod,
      items: ticketItems.map((i) => ({
        product_id: i.product.id,
        cantidad: i.cantidad,
      })),
    })
  }

  return (
    <div className="flex gap-6 h-full min-h-0">
      {/* Left: product browser */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 mb-4 shrink-0">
          <input
            type="text"
            placeholder="Buscar producto..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            <option value="">Todas las categorías</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <p className="text-gray-400 text-sm">Cargando...</p>
          ) : isError ? (
            <p className="text-red-500 text-sm">Error al cargar los productos.</p>
          ) : filtered.length === 0 ? (
            <p className="text-gray-400 text-sm py-12 text-center">No hay productos</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 pb-4">
              {filtered.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAdd={() => handleAddToTicket(product)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: ticket panel */}
      <div className="w-80 shrink-0">
        <TicketPanel
          items={ticketItems}
          onIncrement={handleIncrement}
          onDecrement={handleDecrement}
          onRemove={handleRemove}
          paymentMethod={paymentMethod}
          onPaymentChange={setPaymentMethod}
          onConfirm={handleConfirm}
          isSubmitting={saleMutation.isPending}
          error={error}
          successMessage={successMessage}
        />
      </div>
    </div>
  )
}
