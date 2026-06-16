import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getCategories } from '../api/categories'
import { deleteProduct, getProducts } from '../api/products'
import type { ProductOut } from '../api/products'
import ProductCard from '../components/ProductCard'
import ProductFormModal from '../components/ProductFormModal'
import { useAuthStore } from '../store/authStore'

export default function CatalogPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<ProductOut | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const queryClient = useQueryClient()

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const { data: products = [], isLoading, isError } = useQuery({
    queryKey: ['products', categoryFilter],
    queryFn: () =>
      getProducts(categoryFilter ? Number(categoryFilter) : undefined),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteProduct(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
    onError: () => alert('No se pudo eliminar el producto. Inténtalo de nuevo.'),
  })

  const filtered = products.filter((p) =>
    p.nombre.toLowerCase().includes(search.toLowerCase()),
  )

  function handleEdit(product: ProductOut) {
    setEditingProduct(product)
    setModalOpen(true)
  }

  function handleDelete(id: number) {
    if (window.confirm('¿Eliminar este producto?')) {
      setDeletingId(id)
      deleteMutation.mutate(id, {
        onSettled: () => setDeletingId(null),
      })
    }
  }

  function handleOpenCreate() {
    setEditingProduct(null)
    setModalOpen(true)
  }

  function handleModalClose() {
    setModalOpen(false)
    setEditingProduct(null)
  }

  function handleSaved() {
    queryClient.invalidateQueries({ queryKey: ['products'] })
    handleModalClose()
  }

  return (
    <div className="relative min-h-full">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
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

      {/* Product grid */}
      {isLoading ? (
        <p className="text-gray-400 text-sm">Cargando...</p>
      ) : isError ? (
        <p className="text-red-500 text-sm">Error al cargar los productos. Inténtalo de nuevo.</p>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-gray-300">
          <svg
            className="w-16 h-16 mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
            />
          </svg>
          <p className="text-lg">No hay productos</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              isAdmin={isAdmin}
              onEdit={() => handleEdit(product)}
              onDelete={() => handleDelete(product.id)}
            />
          ))}
        </div>
      )}

      {/* FAB */}
      {isAdmin && (
        <button
          onClick={handleOpenCreate}
          className="fixed bottom-6 right-6 w-12 h-12 bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center text-2xl hover:bg-indigo-700 transition-colors"
          title="Nuevo producto"
          aria-label="Nuevo producto"
        >
          +
        </button>
      )}

      {/* Modal */}
      {modalOpen && (
        <ProductFormModal
          key={editingProduct?.id ?? 'new'}
          product={editingProduct}
          categories={categories}
          onClose={handleModalClose}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
