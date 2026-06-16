import { useState } from 'react'
import type { CategoryOut } from '../api/categories'
import type { ProductOut } from '../api/products'
import { createProduct, updateProduct } from '../api/products'

interface Props {
  product: ProductOut | null
  categories: CategoryOut[]
  onClose: () => void
  onSaved: () => void
}

export default function ProductFormModal({ product, categories, onClose, onSaved }: Props) {
  const [form, setForm] = useState({
    nombre: product?.nombre ?? '',
    precio: product?.precio ?? '',
    stock: String(product?.stock ?? 0),
    stock_minimo: String(product?.stock_minimo ?? 0),
    category_id: String(product?.category_id ?? ''),
  })
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.nombre.trim()) return setError('El nombre es obligatorio')
    const precio = parseFloat(form.precio)
    if (isNaN(precio) || precio <= 0) return setError('El precio debe ser mayor que 0')

    setSaving(true)
    setError(null)
    try {
      const payload = {
        nombre: form.nombre.trim(),
        precio: parseFloat(form.precio).toFixed(2),
        stock: parseInt(form.stock) || 0,
        stock_minimo: parseInt(form.stock_minimo) || 0,
        category_id: form.category_id ? parseInt(form.category_id) : null,
      }
      if (product) {
        await updateProduct(product.id, payload)
      } else {
        await createProduct(payload)
      }
      onSaved()
    } catch {
      setError('Error al guardar el producto. Inténtalo de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {product ? 'Editar producto' : 'Nuevo producto'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre *
            </label>
            <input
              name="nombre"
              value={form.nombre}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Precio (€) *
            </label>
            <input
              name="precio"
              type="number"
              step="0.01"
              min="0.01"
              value={form.precio}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stock
              </label>
              <input
                name="stock"
                type="number"
                min="0"
                value={form.stock}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stock mínimo
              </label>
              <input
                name="stock_minimo"
                type="number"
                min="0"
                value={form.stock_minimo}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoría
            </label>
            <select
              name="category_id"
              value={form.category_id}
              onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="">Sin categoría</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 rounded-lg py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-indigo-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
