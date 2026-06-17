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
    expect(screen.getByText('2/10')).toBeInTheDocument()
    expect(screen.getByText('1/5')).toBeInTheDocument()
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

  it('oculta la lista cuando hay error con datos previos (stale guard)', async () => {
    vi.mocked(reportsApi.fetchLowStock)
      .mockResolvedValueOnce([{ id: 1, nombre: 'Café', stock: 2, stock_minimo: 10 }])
      .mockRejectedValueOnce(new Error('Error de red'))

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    function Wrapper({ children }: { children: React.ReactNode }) {
      return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    }

    render(<LowStockWidget />, { wrapper: Wrapper })

    await waitFor(() => expect(screen.getByText('Café')).toBeInTheDocument())

    await queryClient.invalidateQueries({ queryKey: ['reports', 'low-stock'] })

    await waitFor(() =>
      expect(screen.getByText(/error al cargar alertas de stock/i)).toBeInTheDocument(),
    )
    expect(screen.queryByText('Café')).not.toBeInTheDocument()
  })
})
