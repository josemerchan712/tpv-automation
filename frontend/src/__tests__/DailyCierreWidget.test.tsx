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
