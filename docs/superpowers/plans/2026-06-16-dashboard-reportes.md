# Dashboard de Reportes (Fase 7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir la página `/dashboard` al frontend TPV con tres widgets auto-contenidos: cierre de caja del día (con selector de fecha), alertas de stock bajo y top 10 productos más vendidos (con selector de rango de fechas del mes en curso).

**Architecture:** `DashboardPage` es solo layout + botón de actualizar global. Cada widget (`DailyCierreWidget`, `LowStockWidget`, `TopProductsWidget`) gestiona su propia React Query, sus parámetros de fecha y sus estados de carga/error de forma independiente. El botón "Actualizar" invalida todas las queries con prefijo `['reports']`.

**Tech Stack:** React 18, TypeScript strict, Vite, Tailwind CSS, `@tanstack/react-query` v5, Vitest + React Testing Library.

---

## File Map

| Acción | Ruta | Responsabilidad |
|--------|------|-----------------|
| Crear | `frontend/src/api/reports.ts` | Tipos TypeScript + 3 funciones `fetchX` sobre `apiClient` |
| Crear | `frontend/src/components/DailyCierreWidget.tsx` | Widget cierre de caja con selector de fecha |
| Crear | `frontend/src/components/LowStockWidget.tsx` | Widget alertas de stock bajo |
| Crear | `frontend/src/components/TopProductsWidget.tsx` | Widget top 10 productos con rango de fechas |
| Crear | `frontend/src/pages/DashboardPage.tsx` | Grid de layout + botón Actualizar |
| Crear | `frontend/src/__tests__/DailyCierreWidget.test.tsx` | Tests del widget cierre de caja |
| Crear | `frontend/src/__tests__/LowStockWidget.test.tsx` | Tests del widget stock bajo |
| Crear | `frontend/src/__tests__/TopProductsWidget.test.tsx` | Tests del widget top productos |
| Modificar | `frontend/src/App.tsx` | Añadir ruta `/dashboard` |
| Modificar | `frontend/src/components/Sidebar.tsx` | Añadir enlace "Dashboard" |

---

## Task 1: Capa API (`src/api/reports.ts`)

**Files:**
- Create: `frontend/src/api/reports.ts`

No hay lógica de negocio aquí — son wrappers tipados sobre `apiClient.get`. No se usa TDD para wrappers HTTP puros.

- [ ] **Step 1: Crear `frontend/src/api/reports.ts`**

```ts
import { apiClient } from './client'

export interface PaymentBreakdown {
  efectivo: string
  tarjeta: string
  bizum: string
  otro: string
}

export interface DailyCloseOut {
  fecha: string
  total_ventas: string
  num_tickets: number
  desglose_pago: PaymentBreakdown
}

export interface LowStockProductOut {
  id: number
  nombre: string
  stock: number
  stock_minimo: number
}

export interface TopProductOut {
  product_id: number
  nombre: string
  total_cantidad: number
  total_importe: string
}

export const fetchDailyClose = (fecha: string) =>
  apiClient.get<DailyCloseOut>(`/reports/daily-close?fecha=${fecha}`)

export const fetchLowStock = () =>
  apiClient.get<LowStockProductOut[]>('/reports/low-stock')

export const fetchTopProducts = (fechaDesde: string, fechaHasta: string) =>
  apiClient.get<TopProductOut[]>(
    `/reports/top-products?fecha_desde=${fechaDesde}&fecha_hasta=${fechaHasta}`,
  )
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/reports.ts
git commit -m "feat: add reports API types and fetch functions"
```

---

## Task 2: `DailyCierreWidget` (TDD)

**Files:**
- Create: `frontend/src/__tests__/DailyCierreWidget.test.tsx`
- Create: `frontend/src/components/DailyCierreWidget.tsx`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/__tests__/DailyCierreWidget.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DailyCierreWidget from '../components/DailyCierreWidget'
import * as reportsApi from '../api/reports'

vi.mock('../api/reports')

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
  return Wrapper
}

describe('DailyCierreWidget', () => {
  beforeEach(() => vi.clearAllMocks())

  it('muestra "Cargando..." mientras carga', () => {
    vi.mocked(reportsApi.fetchDailyClose).mockReturnValue(new Promise(() => {}))
    render(<DailyCierreWidget />, { wrapper: makeWrapper() })
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('muestra estado vacío cuando num_tickets es 0', async () => {
    vi.mocked(reportsApi.fetchDailyClose).mockResolvedValue({
      fecha: '2026-06-16',
      total_ventas: '0',
      num_tickets: 0,
      desglose_pago: { efectivo: '0', tarjeta: '0', bizum: '0', otro: '0' },
    })
    render(<DailyCierreWidget />, { wrapper: makeWrapper() })
    await waitFor(() =>
      expect(screen.getByText(/sin ventas para esta fecha/i)).toBeInTheDocument(),
    )
  })

  it('muestra total ventas y nº tickets cuando hay datos', async () => {
    vi.mocked(reportsApi.fetchDailyClose).mockResolvedValue({
      fecha: '2026-06-16',
      total_ventas: '150.50',
      num_tickets: 5,
      desglose_pago: { efectivo: '100.00', tarjeta: '50.50', bizum: '0', otro: '0' },
    })
    render(<DailyCierreWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('150.50 €')).toBeInTheDocument())
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('muestra las cuatro filas de desglose por método de pago', async () => {
    vi.mocked(reportsApi.fetchDailyClose).mockResolvedValue({
      fecha: '2026-06-16',
      total_ventas: '150.50',
      num_tickets: 3,
      desglose_pago: { efectivo: '100.00', tarjeta: '50.50', bizum: '0.00', otro: '0.00' },
    })
    render(<DailyCierreWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('100.00 €')).toBeInTheDocument())
    expect(screen.getByText('50.50 €')).toBeInTheDocument()
    expect(screen.getAllByText('0.00 €')).toHaveLength(2)
  })

  it('llama a fetchDailyClose con la nueva fecha al cambiar el input', async () => {
    vi.mocked(reportsApi.fetchDailyClose).mockResolvedValue({
      fecha: '2026-06-16',
      total_ventas: '0',
      num_tickets: 0,
      desglose_pago: { efectivo: '0', tarjeta: '0', bizum: '0', otro: '0' },
    })
    render(<DailyCierreWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(reportsApi.fetchDailyClose).toHaveBeenCalledTimes(1))
    const input = document.querySelector('input[type="date"]') as HTMLInputElement
    fireEvent.change(input, { target: { value: '2026-06-01' } })
    await waitFor(() =>
      expect(reportsApi.fetchDailyClose).toHaveBeenCalledWith('2026-06-01'),
    )
  })

  it('muestra error cuando la API falla', async () => {
    vi.mocked(reportsApi.fetchDailyClose).mockRejectedValue(new Error('Error de red'))
    render(<DailyCierreWidget />, { wrapper: makeWrapper() })
    await waitFor(() =>
      expect(screen.getByText(/error al cargar el cierre de caja/i)).toBeInTheDocument(),
    )
  })
})
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
cd frontend
npm run test -- --run src/__tests__/DailyCierreWidget.test.tsx
```

Expected: `FAIL` — `Cannot find module '../components/DailyCierreWidget'`

- [ ] **Step 3: Implementar `frontend/src/components/DailyCierreWidget.tsx`**

```tsx
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
          className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {isLoading && <p className="text-gray-400 text-sm">Cargando...</p>}
      {isError && (
        <p className="text-red-500 text-sm">Error al cargar el cierre de caja.</p>
      )}
      {data && data.num_tickets === 0 && (
        <p className="text-gray-400 text-sm py-4 text-center">
          Sin ventas para esta fecha.
        </p>
      )}
      {data && data.num_tickets > 0 && (
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
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
cd frontend
npm run test -- --run src/__tests__/DailyCierreWidget.test.tsx
```

Expected: 6 tests `PASS`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/__tests__/DailyCierreWidget.test.tsx frontend/src/components/DailyCierreWidget.tsx
git commit -m "feat: add DailyCierreWidget with tests"
```

---

## Task 3: `LowStockWidget` (TDD)

**Files:**
- Create: `frontend/src/__tests__/LowStockWidget.test.tsx`
- Create: `frontend/src/components/LowStockWidget.tsx`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/__tests__/LowStockWidget.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LowStockWidget from '../components/LowStockWidget'
import * as reportsApi from '../api/reports'

vi.mock('../api/reports')

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
  return Wrapper
}

describe('LowStockWidget', () => {
  beforeEach(() => vi.clearAllMocks())

  it('muestra "Cargando..." mientras carga', () => {
    vi.mocked(reportsApi.fetchLowStock).mockReturnValue(new Promise(() => {}))
    render(<LowStockWidget />, { wrapper: makeWrapper() })
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('muestra mensaje "Sin alertas" cuando el array está vacío', async () => {
    vi.mocked(reportsApi.fetchLowStock).mockResolvedValue([])
    render(<LowStockWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText(/sin alertas/i)).toBeInTheDocument())
  })

  it('muestra lista de productos con stock bajo', async () => {
    vi.mocked(reportsApi.fetchLowStock).mockResolvedValue([
      { id: 1, nombre: 'Café', stock: 2, stock_minimo: 10 },
      { id: 2, nombre: 'Azúcar', stock: 1, stock_minimo: 5 },
    ])
    render(<LowStockWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('Café')).toBeInTheDocument())
    expect(screen.getByText('Azúcar')).toBeInTheDocument()
  })

  it('muestra badge "Sin stock" para productos con stock 0', async () => {
    vi.mocked(reportsApi.fetchLowStock).mockResolvedValue([
      { id: 1, nombre: 'Azúcar', stock: 0, stock_minimo: 5 },
    ])
    render(<LowStockWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('Sin stock')).toBeInTheDocument())
  })

  it('no muestra badge "Sin stock" para productos con stock > 0', async () => {
    vi.mocked(reportsApi.fetchLowStock).mockResolvedValue([
      { id: 1, nombre: 'Café', stock: 3, stock_minimo: 10 },
    ])
    render(<LowStockWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('Café')).toBeInTheDocument())
    expect(screen.queryByText('Sin stock')).not.toBeInTheDocument()
  })

  it('muestra error cuando la API falla', async () => {
    vi.mocked(reportsApi.fetchLowStock).mockRejectedValue(new Error('Error de red'))
    render(<LowStockWidget />, { wrapper: makeWrapper() })
    await waitFor(() =>
      expect(screen.getByText(/error al cargar alertas de stock/i)).toBeInTheDocument(),
    )
  })
})
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
cd frontend
npm run test -- --run src/__tests__/LowStockWidget.test.tsx
```

Expected: `FAIL` — `Cannot find module '../components/LowStockWidget'`

- [ ] **Step 3: Implementar `frontend/src/components/LowStockWidget.tsx`**

```tsx
import { useQuery } from '@tanstack/react-query'
import { fetchLowStock } from '../api/reports'

export default function LowStockWidget() {
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ['reports', 'low-stock'],
    queryFn: fetchLowStock,
  })

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h2 className="font-semibold text-gray-800 mb-4">Alertas de Stock</h2>

      {isLoading && <p className="text-gray-400 text-sm">Cargando...</p>}
      {isError && (
        <p className="text-red-500 text-sm">Error al cargar alertas de stock.</p>
      )}
      {!isLoading && !isError && data.length === 0 && (
        <p className="text-gray-400 text-sm py-4 text-center">
          Sin alertas — todos los productos tienen stock suficiente.
        </p>
      )}
      {data.length > 0 && (
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
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
cd frontend
npm run test -- --run src/__tests__/LowStockWidget.test.tsx
```

Expected: 6 tests `PASS`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/__tests__/LowStockWidget.test.tsx frontend/src/components/LowStockWidget.tsx
git commit -m "feat: add LowStockWidget with tests"
```

---

## Task 4: `TopProductsWidget` (TDD)

**Files:**
- Create: `frontend/src/__tests__/TopProductsWidget.test.tsx`
- Create: `frontend/src/components/TopProductsWidget.tsx`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `frontend/src/__tests__/TopProductsWidget.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TopProductsWidget from '../components/TopProductsWidget'
import * as reportsApi from '../api/reports'

vi.mock('../api/reports')

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
  return Wrapper
}

describe('TopProductsWidget', () => {
  beforeEach(() => vi.clearAllMocks())

  it('muestra "Cargando..." mientras carga', () => {
    vi.mocked(reportsApi.fetchTopProducts).mockReturnValue(new Promise(() => {}))
    render(<TopProductsWidget />, { wrapper: makeWrapper() })
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('muestra "Sin ventas en este período" cuando el array está vacío', async () => {
    vi.mocked(reportsApi.fetchTopProducts).mockResolvedValue([])
    render(<TopProductsWidget />, { wrapper: makeWrapper() })
    await waitFor(() =>
      expect(screen.getByText(/sin ventas en este período/i)).toBeInTheDocument(),
    )
  })

  it('muestra ranking con posición, nombre, unidades e importe', async () => {
    vi.mocked(reportsApi.fetchTopProducts).mockResolvedValue([
      { product_id: 1, nombre: 'Café', total_cantidad: 50, total_importe: '75.00' },
      { product_id: 2, nombre: 'Agua', total_cantidad: 30, total_importe: '24.00' },
    ])
    render(<TopProductsWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('Café')).toBeInTheDocument())
    expect(screen.getByText('Agua')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('75.00 €')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('muestra máximo 10 productos aunque la API devuelva más', async () => {
    const products = Array.from({ length: 15 }, (_, i) => ({
      product_id: i + 1,
      nombre: `Producto ${i + 1}`,
      total_cantidad: 100 - i,
      total_importe: '10.00',
    }))
    vi.mocked(reportsApi.fetchTopProducts).mockResolvedValue(products)
    render(<TopProductsWidget />, { wrapper: makeWrapper() })
    await waitFor(() => expect(screen.getByText('Producto 1')).toBeInTheDocument())
    expect(screen.queryByText('Producto 11')).not.toBeInTheDocument()
  })

  it('los inputs de fecha tienen valores por defecto del mes en curso', async () => {
    vi.mocked(reportsApi.fetchTopProducts).mockResolvedValue([])
    render(<TopProductsWidget />, { wrapper: makeWrapper() })
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const lastDay = new Date(year, now.getMonth() + 1, 0).getDate()
    const expectedDesde = `${year}-${month}-01`
    const expectedHasta = `${year}-${month}-${String(lastDay).padStart(2, '0')}`
    expect(screen.getByDisplayValue(expectedDesde)).toBeInTheDocument()
    expect(screen.getByDisplayValue(expectedHasta)).toBeInTheDocument()
  })

  it('muestra error cuando la API falla', async () => {
    vi.mocked(reportsApi.fetchTopProducts).mockRejectedValue(new Error('Error de red'))
    render(<TopProductsWidget />, { wrapper: makeWrapper() })
    await waitFor(() =>
      expect(
        screen.getByText(/error al cargar el ranking de productos/i),
      ).toBeInTheDocument(),
    )
  })
})
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
cd frontend
npm run test -- --run src/__tests__/TopProductsWidget.test.tsx
```

Expected: `FAIL` — `Cannot find module '../components/TopProductsWidget'`

- [ ] **Step 3: Implementar `frontend/src/components/TopProductsWidget.tsx`**

```tsx
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
  const { desde, hasta } = getMonthRange()
  const [fechaDesde, setFechaDesde] = useState(desde)
  const [fechaHasta, setFechaHasta] = useState(hasta)

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
      {top10.length > 0 && (
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
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
cd frontend
npm run test -- --run src/__tests__/TopProductsWidget.test.tsx
```

Expected: 6 tests `PASS`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/__tests__/TopProductsWidget.test.tsx frontend/src/components/TopProductsWidget.tsx
git commit -m "feat: add TopProductsWidget with tests"
```

---

## Task 5: `DashboardPage` + ruta + sidebar

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`

No hay lógica de negocio en `DashboardPage` (solo layout + invalidación). No se aplica TDD.

- [ ] **Step 1: Crear `frontend/src/pages/DashboardPage.tsx`**

```tsx
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
```

- [ ] **Step 2: Añadir ruta `/dashboard` en `frontend/src/App.tsx`**

El archivo actual es:

```tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import CatalogPage from './pages/CatalogPage'
import SalesPage from './pages/SalesPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/catalogo" replace />} />
              <Route path="/catalogo" element={<CatalogPage />} />
              <Route path="/ventas" element={<SalesPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

Sustituirlo por:

```tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import CatalogPage from './pages/CatalogPage'
import SalesPage from './pages/SalesPage'
import DashboardPage from './pages/DashboardPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/catalogo" replace />} />
              <Route path="/catalogo" element={<CatalogPage />} />
              <Route path="/ventas" element={<SalesPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 3: Añadir enlace "Dashboard" en `frontend/src/components/Sidebar.tsx`**

El archivo actual es:

```tsx
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = user?.username.slice(0, 2).toUpperCase() ?? '??'

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="p-4 border-b border-gray-200">
        <span className="font-bold text-lg text-indigo-600">TPV</span>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <NavLink
          to="/catalogo"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Catálogo
        </NavLink>

        <NavLink
          to="/ventas"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Ventas
        </NavLink>
      </nav>

      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
            {initials}
          </div>
          <span className="text-sm text-gray-700 truncate">{user?.username}</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-500 transition-colors"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
```

Sustituirlo por (se añade el NavLink de Dashboard como primer elemento del `<nav>`):

```tsx
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = user?.username.slice(0, 2).toUpperCase() ?? '??'

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="p-4 border-b border-gray-200">
        <span className="font-bold text-lg text-indigo-600">TPV</span>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Dashboard
        </NavLink>

        <NavLink
          to="/catalogo"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Catálogo
        </NavLink>

        <NavLink
          to="/ventas"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Ventas
        </NavLink>
      </nav>

      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
            {initials}
          </div>
          <span className="text-sm text-gray-700 truncate">{user?.username}</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-500 transition-colors"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
```

- [ ] **Step 4: Verificar que la suite completa pasa sin regresiones**

```bash
cd frontend
npm run test -- --run
```

Expected: todos los tests `PASS` (TicketPanel + DailyCierreWidget + LowStockWidget + TopProductsWidget)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx frontend/src/App.tsx frontend/src/components/Sidebar.tsx
git commit -m "feat: add DashboardPage, /dashboard route and sidebar link"
```

---

## Self-Review

### Spec coverage

| Requisito del spec | Tarea que lo implementa |
|---|---|
| Nueva sección "Dashboard" en el sidebar | Task 5 — Sidebar.tsx |
| Ruta `/dashboard` | Task 5 — App.tsx |
| Widget cierre de caja: total ventas, desglose, nº tickets | Task 2 — DailyCierreWidget |
| Selector de fecha en cierre de caja | Task 2 — DailyCierreWidget |
| Widget alertas de stock bajo | Task 3 — LowStockWidget |
| Badge rojo para stock === 0 | Task 3 — LowStockWidget |
| Widget top productos con selector de rango de fechas | Task 4 — TopProductsWidget |
| Rango por defecto = mes en curso | Task 4 — TopProductsWidget |
| Máximo 10 productos | Task 4 — TopProductsWidget (`.slice(0, 10)`) |
| Botón "Actualizar" global | Task 5 — DashboardPage |
| `invalidateQueries(['reports'])` en actualizar | Task 5 — DashboardPage |
| Estado "Cargando..." | Tasks 2, 3, 4 — todos los widgets |
| Estado "sin datos" por widget | Tasks 2, 3, 4 — mensajes específicos |
| Estado de error por widget | Tasks 2, 3, 4 — mensajes de error |
| `parseFloat(v).toFixed(2)` para importes | Tasks 2, 4 — función `fmt()` local |
| Tipos TypeScript alineados con backend | Task 1 — `reports.ts` |

### Placeholder scan

Ningún TBD, TODO, ni paso sin código encontrado.

### Type consistency

- `DailyCloseOut.desglose_pago` es `PaymentBreakdown` → `DailyCierreWidget` accede via `data.desglose_pago[method]` donde `method` es `'efectivo' | 'tarjeta' | 'bizum' | 'otro'` — consistente con `PaymentBreakdown`.
- `fetchDailyClose(fecha: string)` llamado en `DailyCierreWidget` con `fecha` de tipo `string` — consistente.
- `fetchTopProducts(fechaDesde, fechaHasta)` llamado en `TopProductsWidget` con los dos strings — consistente.
- `LowStockProductOut.stock_minimo` mostrado en `LowStockWidget` — consistente.
- `TopProductOut.total_importe` formateado con `fmt()` en `TopProductsWidget` — consistente.
- Query key prefix `['reports']` usado en los tres widgets y en `invalidateQueries` en `DashboardPage` — consistente.
