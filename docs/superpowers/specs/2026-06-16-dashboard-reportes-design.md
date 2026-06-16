# Dashboard de Reportes — Spec de Diseño (Fase 7)

**Fecha:** 2026-06-16  
**Rama:** feat/phase5-reports  
**Autor:** José María Merchán Martos

---

## Objetivo

Añadir una sección "Dashboard" al frontend del TPV que consolide los tres reportes del backend en una pantalla única de consulta rápida: cierre de caja del día (con selector de fecha), alertas de stock bajo y ranking de top 10 productos más vendidos (con selector de rango de fechas).

---

## Contexto

El backend ya expone tres endpoints autenticados en `/reports`:

| Endpoint | Parámetros | Respuesta |
|---|---|---|
| `GET /reports/daily-close` | `fecha` (opcional, default hoy) | `DailyCloseOut` |
| `GET /reports/low-stock` | — | `LowStockProductOut[]` |
| `GET /reports/top-products` | `fecha_desde`, `fecha_hasta` (opcionales) | `TopProductOut[]` |

El frontend usa React Query (`@tanstack/react-query`) para estado del servidor y Tailwind CSS con paleta indigo/gray para UI.

---

## Arquitectura

### Enfoque elegido

**DashboardPage + 3 componentes widget auto-contenidos.** `DashboardPage` es solo layout y el botón de actualizar global. Cada widget gestiona su propia query, sus propios parámetros de fecha y sus propios estados de carga/error. Los widgets fallan de forma independiente.

### Ficheros nuevos

```
frontend/src/
├── api/
│   └── reports.ts
├── pages/
│   └── DashboardPage.tsx
└── components/
    ├── DailyCierreWidget.tsx
    ├── LowStockWidget.tsx
    └── TopProductsWidget.tsx
```

### Ficheros modificados

| Fichero | Cambio |
|---|---|
| `src/App.tsx` | Añadir ruta `/dashboard` → `<DashboardPage />` |
| `src/components/Sidebar.tsx` | Añadir enlace "Dashboard" con `NavLink` |

Sin cambios en backend. Sin nuevas dependencias de npm.

---

## Componentes

### `src/api/reports.ts`

Tres funciones tipadas sobre `apiClient`:

```ts
fetchDailyClose(fecha: string): Promise<DailyCloseOut>
fetchLowStock(): Promise<LowStockProductOut[]>
fetchTopProducts(fechaDesde: string, fechaHasta: string): Promise<TopProductOut[]>
```

Tipos locales que reflejan los schemas del backend (`total_ventas: string` porque Decimal serializa como string JSON):

```ts
interface PaymentBreakdown {
  efectivo: string; tarjeta: string; bizum: string; otro: string
}
interface DailyCloseOut {
  fecha: string; total_ventas: string; num_tickets: number; desglose_pago: PaymentBreakdown
}
interface LowStockProductOut {
  id: number; nombre: string; stock: number; stock_minimo: number
}
interface TopProductOut {
  product_id: number; nombre: string; total_cantidad: number; total_importe: string
}
```

---

### `DashboardPage.tsx`

Layout único: fila superior con `DailyCierreWidget` a ancho completo; fila inferior con `LowStockWidget` y `TopProductsWidget` en dos columnas iguales.

Botón "Actualizar" en la cabecera de la página que llama a:
```ts
queryClient.invalidateQueries({ queryKey: ['reports'] })
```
Esto dispara el refetch de los tres widgets simultáneamente (todos usan query keys con prefijo `['reports', ...]`).

No hay auto-refresh. Los datos se cargan al entrar a la ruta y solo se actualizan al pulsar el botón.

---

### `DailyCierreWidget.tsx`

**Estado local:** `fecha: string` inicializado a hoy (`new Date().toISOString().slice(0, 10)`).

**Query key:** `['reports', 'daily-close', fecha]` — React Query refetch automático al cambiar la fecha.

**UI de la card:**
- Cabecera: título "Cierre de Caja" + `<input type="date">` alineado a la derecha
- Métricas principales: total ventas en tipografía grande, nº tickets en secundario
- Tabla de desglose: cuatro filas (Efectivo / Tarjeta / Bizum / Otro) con importe en cada una
- Estado vacío (`num_tickets === 0`): "Sin ventas para esta fecha"

---

### `LowStockWidget.tsx`

**Sin estado local ni parámetros de fecha.**

**Query key:** `['reports', 'low-stock']`

**UI de la card:**
- Cabecera: título "Alertas de Stock"
- Lista de productos: nombre, stock actual, stock mínimo
- Badge rojo en los productos con `stock === 0`
- Estado vacío: "Sin alertas de stock — todos los productos tienen stock suficiente"

---

### `TopProductsWidget.tsx`

**Estado local:** `fechaDesde` y `fechaHasta` inicializados al primer y último día del mes en curso.

**Query key:** `['reports', 'top-products', fechaDesde, fechaHasta]`

**UI de la card:**
- Cabecera: título "Top Productos" + dos `<input type="date">` (Desde / Hasta)
- Validación mínima: atributo `max` de `fechaDesde` = `fechaHasta`, y `min` de `fechaHasta` = `fechaDesde`
- Tabla numerada (1-10): posición, nombre del producto, unidades vendidas, importe total
- Estado vacío: "Sin ventas en este período"
- La API ya limita a los más vendidos; el frontend muestra máximo 10 filas (`.slice(0, 10)`)

---

## Manejo de estados

Patrón uniforme en los tres widgets:

| Estado | Render |
|---|---|
| `isLoading` | Texto "Cargando..." en gris dentro de la card |
| `isError` | Mensaje de error en rojo (mensaje normalizado por `apiClient`) |
| Datos vacíos | Mensaje neutro específico por widget |
| Datos OK | Contenido del widget |

Los tres widgets fallan de forma independiente: un error en uno no bloquea los otros dos.

---

## Layout visual (texto)

```
┌─────────────────────────────────────────────────────┐
│ Dashboard                          [Actualizar]      │
├─────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────┐   │
│ │  Cierre de Caja              [input: fecha]   │   │
│ │                                               │   │
│ │  Total: €1.234,50          Tickets: 47        │   │
│ │  ─────────────────────────────────────────    │   │
│ │  Efectivo   €400,00                           │   │
│ │  Tarjeta    €700,50                           │   │
│ │  Bizum      €134,00                           │   │
│ │  Otro       €0,00                             │   │
│ └───────────────────────────────────────────────┘   │
│                                                     │
│ ┌─────────────────────┐  ┌─────────────────────┐   │
│ │  Alertas de Stock   │  │  Top Productos       │   │
│ │                     │  │  [Desde] [Hasta]     │   │
│ │  • Café (2/10)  🔴  │  │  1. Producto A  50u  │   │
│ │  • Azúcar (0/5) 🔴  │  │  2. Producto B  38u  │   │
│ │  ...                │  │  ...                 │   │
│ └─────────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Testing

Patrón: Vitest + React Testing Library, mock de `apiClient`, igual que `TicketPanel.test.tsx`.

### `DailyCierreWidget.test.tsx`
- Render de total ventas y nº tickets con datos mock
- Render de las cuatro filas de desglose de pago
- Estado vacío cuando `num_tickets === 0`
- Cambiar el input de fecha dispara nueva query (query key distinta)

### `LowStockWidget.test.tsx`
- Lista de productos con stock bajo
- Badge rojo visible cuando `stock === 0`
- Mensaje "Sin alertas" cuando el array está vacío

### `TopProductsWidget.test.tsx`
- Tabla con ranking de productos (posición, nombre, unidades, importe)
- Los inputs de fecha tienen valores por defecto del mes en curso
- Muestra máximo 10 filas aunque la API devuelva más

`DashboardPage` no tiene unit tests propios (es solo layout); los widgets se cubren en aislamiento.

---

## Decisiones y restricciones

- `<input type="date">` nativo: sin dependencias extra de date-picker
- Decimal → `string` en JSON: los importes se muestran tal cual desde la API (ya vienen formateados con dos decimales)
- Top 10: la limitación se aplica en el frontend con `.slice(0, 10)` ya que el backend no tiene parámetro `limit`
- El botón "Actualizar" invalida todas las queries con prefijo `['reports']`, lo que garantiza coherencia de datos entre los tres widgets
