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
