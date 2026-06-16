import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TicketPanel from '../components/TicketPanel'
import type { TicketItem } from '../components/TicketPanel'

const noop = () => {}

const sampleItems: TicketItem[] = [
  {
    product: {
      id: 1,
      nombre: 'Café',
      precio: '1.50',
      stock: 10,
      stock_minimo: 2,
      category_id: null,
      category: null,
    },
    cantidad: 2,
  },
  {
    product: {
      id: 2,
      nombre: 'Agua',
      precio: '0.80',
      stock: 5,
      stock_minimo: 1,
      category_id: null,
      category: null,
    },
    cantidad: 1,
  },
]

describe('TicketPanel', () => {
  it('muestra mensaje vacío cuando no hay items', () => {
    render(
      <TicketPanel
        items={[]}
        onIncrement={noop}
        onDecrement={noop}
        onRemove={noop}
        paymentMethod="efectivo"
        onPaymentChange={noop}
        onConfirm={noop}
        isSubmitting={false}
        error={null}
        successMessage={null}
      />,
    )
    expect(screen.getByText(/añade productos/i)).toBeInTheDocument()
  })

  it('calcula y muestra el total correcto', () => {
    // 2 × 1.50 + 1 × 0.80 = 3.80
    render(
      <TicketPanel
        items={sampleItems}
        onIncrement={noop}
        onDecrement={noop}
        onRemove={noop}
        paymentMethod="efectivo"
        onPaymentChange={noop}
        onConfirm={noop}
        isSubmitting={false}
        error={null}
        successMessage={null}
      />,
    )
    expect(screen.getByText('3.80 €')).toBeInTheDocument()
  })

  it('botón confirmar está deshabilitado cuando no hay items', () => {
    render(
      <TicketPanel
        items={[]}
        onIncrement={noop}
        onDecrement={noop}
        onRemove={noop}
        paymentMethod="efectivo"
        onPaymentChange={noop}
        onConfirm={noop}
        isSubmitting={false}
        error={null}
        successMessage={null}
      />,
    )
    expect(screen.getByRole('button', { name: /confirmar venta/i })).toBeDisabled()
  })

  it('llama a onRemove al hacer click en quitar', async () => {
    const onRemove = vi.fn()
    render(
      <TicketPanel
        items={sampleItems}
        onIncrement={noop}
        onDecrement={noop}
        onRemove={onRemove}
        paymentMethod="efectivo"
        onPaymentChange={noop}
        onConfirm={noop}
        isSubmitting={false}
        error={null}
        successMessage={null}
      />,
    )
    await userEvent.click(screen.getByLabelText(/quitar café/i))
    expect(onRemove).toHaveBeenCalledWith(1)
  })

  it('muestra mensaje de error', () => {
    render(
      <TicketPanel
        items={sampleItems}
        onIncrement={noop}
        onDecrement={noop}
        onRemove={noop}
        paymentMethod="efectivo"
        onPaymentChange={noop}
        onConfirm={noop}
        isSubmitting={false}
        error="Stock insuficiente para Café"
        successMessage={null}
      />,
    )
    expect(screen.getByText('Stock insuficiente para Café')).toBeInTheDocument()
  })
})
