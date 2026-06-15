# Phase 3 — Products & Category Catalog Design

**Date:** 2026-06-15
**Scope:** Backend CRUD API for Products & Categories + Frontend catalog UI with sidebar layout

---

## Goal

Deliver the product catalog management feature end-to-end:
- FastAPI endpoints for Products and Categories with role-based access (admin-only writes)
- React frontend with sidebar layout, login page, and a card-based catalog view reusable in the TPV flow (Phase 4)

---

## Backend

### New Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/categories` | any authenticated | List all categories |
| POST | `/categories` | admin only | Create category |
| PUT | `/categories/{id}` | admin only | Update category |
| DELETE | `/categories/{id}` | admin only | Delete category (only if no products linked) |
| GET | `/products` | any authenticated | List products, optional `?category_id=` filter |
| POST | `/products` | admin only | Create product |
| GET | `/products/{id}` | any authenticated | Product detail |
| PUT | `/products/{id}` | admin only | Update product |
| DELETE | `/products/{id}` | admin only | Delete product |

### Schemas (`backend/app/schemas/`)

**`category.py`**
```python
class CategoryCreate(BaseModel):
    nombre: str

class CategoryOut(BaseModel):
    id: int
    nombre: str
    model_config = {"from_attributes": True}
```

**`product.py`**
```python
class ProductCreate(BaseModel):
    nombre: str
    precio: Decimal  # > 0
    stock: int = 0
    stock_minimo: int = 0
    category_id: int | None = None

class ProductUpdate(BaseModel):
    nombre: str | None = None
    precio: Decimal | None = None
    stock: int | None = None
    stock_minimo: int | None = None
    category_id: int | None = None

class ProductOut(BaseModel):
    id: int
    nombre: str
    precio: Decimal
    stock: int
    stock_minimo: int
    category_id: int | None
    category: CategoryOut | None
    model_config = {"from_attributes": True}
```

### Auth & Authorization

Add `require_admin` dependency to `backend/app/dependencies.py`:
```python
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

All write endpoints (`POST`, `PUT`, `DELETE`) use `Depends(require_admin)`.
Read endpoints use `Depends(get_current_user)`.

### Services

- `backend/app/services/category_service.py` — CRUD functions operating on `Session`
- `backend/app/services/product_service.py` — CRUD functions; DELETE raises 409 if category has products linked (category delete only)

### Routers

- `backend/app/routers/categories.py` — thin HTTP layer, delegates to category_service
- `backend/app/routers/products.py` — thin HTTP layer, delegates to product_service

Both registered in `main.py`.

### Tests

- `backend/tests/test_categories.py` — CRUD happy paths + 403 for non-admin + 409 delete with products linked
- `backend/tests/test_products.py` — CRUD happy paths + category filter + 403 for non-admin + 404 not found

---

## Frontend

### Tech additions

- `@tanstack/react-query` — data fetching, caching, mutation invalidation
- `zustand` — auth store (token + user)

### File Structure

```
frontend/src/
├── api/
│   ├── client.ts         # base fetch wrapper (attaches Authorization header)
│   ├── auth.ts           # login(), getMe()
│   ├── products.ts       # getProducts(), getProduct(), createProduct(), updateProduct(), deleteProduct()
│   └── categories.ts     # getCategories(), createCategory(), updateCategory(), deleteCategory()
├── store/
│   └── authStore.ts      # Zustand: { token, user, setAuth, logout } persisted to localStorage
├── components/
│   ├── Layout.tsx         # Sidebar + <Outlet />
│   ├── Sidebar.tsx        # Nav links, user info, logout button
│   ├── ProtectedRoute.tsx # Redirects to /login if no token
│   ├── ProductCard.tsx    # Card with optional admin controls
│   └── ProductFormModal.tsx  # Create/edit modal (shared)
└── pages/
    ├── LoginPage.tsx
    └── CatalogPage.tsx
```

### Routing

```
/login        → LoginPage (public)
/             → redirect to /catalogo
/catalogo     → ProtectedRoute → Layout → CatalogPage
/ventas       → ProtectedRoute → Layout → placeholder (Phase 4)
```

### Auth Flow

1. `LoginPage` calls `POST /auth/login` → stores `{ token, user }` in Zustand (persisted to `localStorage`)
2. `ProtectedRoute` reads store; redirects to `/login` if no token
3. `Layout` calls `GET /auth/me` on mount to hydrate current user (handles stale token)
4. Logout clears store + redirects to `/login`

### Components

**`ProductCard`**

Props: `product: ProductOut`, `isAdmin: boolean`, `onEdit: () => void`, `onDelete: () => void`

- White card, soft shadow, rounded corners
- Top section: square placeholder (grey background + product SVG icon)
- Body: product name (bold), category badge (colored pill), price (large), stock chip (green if `stock >= stock_minimo`, red otherwise)
- If `isAdmin`: edit (pencil) and delete (trash) icon buttons in top-right corner

**`CatalogPage`**

- Top bar: text search input (filters by name client-side) + category dropdown (sends `?category_id=` to API)
- Grid: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4` with gap
- If admin: floating action button "+" bottom-right to open `ProductFormModal` in create mode
- Empty state: centered icon + "No hay productos" message

**`ProductFormModal`**

- Centered modal overlay
- Fields: nombre (required), precio (required, > 0), stock (default 0), stock mínimo (default 0), categoría (select, optional)
- Client-side validation before submit
- Title: "Nuevo producto" | "Editar producto"
- On save: calls create or update → invalidates `['products']` React Query key → modal closes

**`Sidebar`**

- Top: app logo + name
- Nav links: Catálogo (active), Ventas (disabled, tooltip "Próximamente")
- Bottom: user initials avatar + username + logout button

**`LoginPage`**

- Centered card: logo, username + password fields, "Entrar" button
- Inline error message on 401

---

## Error Handling

| Scenario | Backend | Frontend |
|----------|---------|----------|
| Non-admin tries to write | 403 Forbidden | Toast "Sin permisos de admin" |
| Product not found | 404 Not Found | Toast "Producto no encontrado" |
| Delete category with products | 409 Conflict | Toast "Elimina primero los productos de esta categoría" |
| Invalid token / expired | 401 Unauthorized | Redirect to /login |
| Validation error (Pydantic) | 422 Unprocessable | Form field errors shown inline |

---

## Testing Strategy

**Backend (pytest):**
- All tests use real in-memory SQLite (existing conftest fixture)
- Admin fixture: user with `role=admin` + valid JWT header
- Cashier fixture: user with `role=cashier` + valid JWT header
- Test every endpoint: happy path + auth failure + not found + business rule violations

**Frontend:**
- No automated tests in this phase; manual smoke test of golden paths
- TypeScript strict mode catches type errors at build time

---

## Out of Scope (Phase 3)

- Product images (Phase 4+)
- Stock movement history (Phase 4)
- Sales / orders flow (Phase 4)
- User management UI (later phase)
- Pagination (add when product count warrants it)
