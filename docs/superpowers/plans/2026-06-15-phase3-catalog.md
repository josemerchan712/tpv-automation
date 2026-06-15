# Phase 3 — Products & Category Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver full CRUD API for Products and Categories (admin-only writes) plus a React frontend with sidebar layout, login page, and card-based product catalog.

**Architecture:** Backend follows the existing thin-router + service pattern. Frontend adds react-router-dom, Zustand (auth store persisted to localStorage), and React Query (data fetching). The vite proxy strips `/api` prefix before forwarding to FastAPI. Product cards accept an `isAdmin` prop so the same component works in the TPV flow (Phase 4).

**Tech Stack:** FastAPI, SQLAlchemy (sync), Pydantic v2 · React 19, TypeScript strict, Tailwind v4, react-router-dom v7, zustand v5, @tanstack/react-query v5

---

## File Map

### Backend — new files
| Action | Path |
|--------|------|
| Create | `backend/app/schemas/category.py` |
| Create | `backend/app/schemas/product.py` |
| Modify | `backend/app/dependencies.py` |
| Create | `backend/app/services/category_service.py` |
| Create | `backend/app/services/product_service.py` |
| Create | `backend/app/routers/categories.py` |
| Create | `backend/app/routers/products.py` |
| Modify | `backend/app/main.py` |
| Modify | `backend/tests/conftest.py` |
| Create | `backend/tests/test_categories.py` |
| Create | `backend/tests/test_products.py` |

### Frontend — new files
| Action | Path |
|--------|------|
| Modify | `frontend/vite.config.ts` |
| Create | `frontend/src/api/client.ts` |
| Create | `frontend/src/api/auth.ts` |
| Create | `frontend/src/api/products.ts` |
| Create | `frontend/src/api/categories.ts` |
| Create | `frontend/src/store/authStore.ts` |
| Modify | `frontend/src/App.tsx` |
| Create | `frontend/src/components/ProtectedRoute.tsx` |
| Create | `frontend/src/components/Layout.tsx` |
| Create | `frontend/src/components/Sidebar.tsx` |
| Create | `frontend/src/components/ProductCard.tsx` |
| Create | `frontend/src/components/ProductFormModal.tsx` |
| Create | `frontend/src/pages/LoginPage.tsx` |
| Create | `frontend/src/pages/CatalogPage.tsx` |

---

## Task 1: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/category.py`
- Create: `backend/app/schemas/product.py`

- [ ] **Step 1: Create `backend/app/schemas/category.py`**

```python
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    nombre: str


class CategoryOut(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Create `backend/app/schemas/product.py`**

```python
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.category import CategoryOut


class ProductCreate(BaseModel):
    nombre: str
    precio: Decimal
    stock: int = 0
    stock_minimo: int = 0
    category_id: int | None = None

    @field_validator("precio")
    @classmethod
    def precio_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("precio must be greater than 0")
        return v


class ProductUpdate(BaseModel):
    nombre: str | None = None
    precio: Decimal | None = None
    stock: int | None = None
    stock_minimo: int | None = None
    category_id: int | None = None

    @field_validator("precio")
    @classmethod
    def precio_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("precio must be greater than 0")
        return v


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

- [ ] **Step 3: Verify Python parses both files without errors**

```bash
cd backend
.venv/Scripts/python -c "from app.schemas.category import CategoryCreate, CategoryOut; from app.schemas.product import ProductCreate, ProductUpdate, ProductOut; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/category.py backend/app/schemas/product.py
git commit -m "feat(catalog): add Pydantic schemas for Category and Product"
```

---

## Task 2: `require_admin` Dependency

**Files:**
- Modify: `backend/app/dependencies.py`

- [ ] **Step 1: Add `require_admin` to `backend/app/dependencies.py`**

Replace the entire file with:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import decode_access_token, get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
```

- [ ] **Step 2: Run the existing test suite to confirm nothing broke**

```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```

Expected: all existing tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend/app/dependencies.py
git commit -m "feat(catalog): add require_admin FastAPI dependency"
```

---

## Task 3: Category Service + Tests (TDD)

**Files:**
- Modify: `backend/tests/conftest.py`
- Create: `backend/app/services/category_service.py`
- Create: `backend/tests/test_categories.py`

- [ ] **Step 1: Add shared auth fixtures to `backend/tests/conftest.py`**

Append these fixtures to the end of the existing file:

```python
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash


@pytest.fixture
def admin_user(db):
    user = User(
        username="admin_test",
        password_hash=get_password_hash("admin123"),
        role=UserRole.admin,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def cashier_user(db):
    user = User(
        username="cashier_test",
        password_hash=get_password_hash("cash123"),
        role=UserRole.cashier,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def admin_headers(client, admin_user):
    resp = client.post(
        "/auth/login", json={"username": "admin_test", "password": "admin123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cashier_headers(client, cashier_user):
    resp = client.post(
        "/auth/login", json={"username": "cashier_test", "password": "cash123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 2: Write failing tests in `backend/tests/test_categories.py`**

```python
import pytest
from decimal import Decimal
from app.models.product import Product


def test_list_categories_authenticated(client, admin_headers):
    resp = client.get("/categories", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_categories_unauthenticated(client):
    resp = client.get("/categories")
    assert resp.status_code == 401


def test_create_category_admin(client, admin_headers):
    resp = client.post("/categories", json={"nombre": "Bebidas"}, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "Bebidas"
    assert "id" in data


def test_create_category_cashier_forbidden(client, cashier_headers):
    resp = client.post(
        "/categories", json={"nombre": "Bebidas"}, headers=cashier_headers
    )
    assert resp.status_code == 403


def test_update_category_admin(client, admin_headers):
    create = client.post(
        "/categories", json={"nombre": "Comida"}, headers=admin_headers
    )
    cat_id = create.json()["id"]
    resp = client.put(
        f"/categories/{cat_id}", json={"nombre": "Comida Rápida"}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Comida Rápida"


def test_update_category_not_found(client, admin_headers):
    resp = client.put(
        "/categories/9999", json={"nombre": "X"}, headers=admin_headers
    )
    assert resp.status_code == 404


def test_delete_category_admin(client, admin_headers):
    create = client.post(
        "/categories", json={"nombre": "ParaBorrar"}, headers=admin_headers
    )
    cat_id = create.json()["id"]
    resp = client.delete(f"/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_delete_category_not_found(client, admin_headers):
    resp = client.delete("/categories/9999", headers=admin_headers)
    assert resp.status_code == 404


def test_delete_category_with_products_conflict(client, admin_headers, db):
    create = client.post(
        "/categories", json={"nombre": "ConProductos"}, headers=admin_headers
    )
    cat_id = create.json()["id"]
    product = Product(nombre="Producto Test", precio=Decimal("5.00"), category_id=cat_id)
    db.add(product)
    db.flush()
    resp = client.delete(f"/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 409
```

- [ ] **Step 3: Run tests — expect FAIL (404 on all category endpoints)**

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_categories.py -v
```

Expected: all tests fail with connection errors or 404 (router not registered yet).

- [ ] **Step 4: Create `backend/app/services/category_service.py`**

```python
from sqlalchemy.orm import Session

from app.models.category import Category


def get_all_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.nombre).all()


def get_category(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(db: Session, nombre: str) -> Category:
    category = Category(nombre=nombre)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, nombre: str) -> Category | None:
    category = get_category(db, category_id)
    if category is None:
        return None
    category.nombre = nombre
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    category = get_category(db, category_id)
    if category is None:
        return False
    if category.products:
        raise ValueError("Category has linked products")
    db.delete(category)
    db.commit()
    return True
```

- [ ] **Step 5: Create `backend/app/routers/categories.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return category_service.get_all_categories(db)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return category_service.create_category(db, payload.nombre)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    category = category_service.update_category(db, category_id, payload.nombre)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        found = category_service.delete_category(db, category_id)
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete category with associated products",
        )
    if not found:
        raise HTTPException(status_code=404, detail="Category not found")
```

- [ ] **Step 6: Register the categories router in `backend/app/main.py`**

Replace the entire file:

```python
import logging
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401
from app.routers import auth, categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY == "change-me-in-production":
        warnings.warn(
            "SECRET_KEY is using the insecure default value. "
            "Set the SECRET_KEY environment variable before deploying to production.",
            stacklevel=2,
        )
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="TPV Automation", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(categories.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Run category tests — expect all PASS**

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_categories.py -v
```

Expected:
```
PASSED tests/test_categories.py::test_list_categories_authenticated
PASSED tests/test_categories.py::test_list_categories_unauthenticated
PASSED tests/test_categories.py::test_create_category_admin
PASSED tests/test_categories.py::test_create_category_cashier_forbidden
PASSED tests/test_categories.py::test_update_category_admin
PASSED tests/test_categories.py::test_update_category_not_found
PASSED tests/test_categories.py::test_delete_category_admin
PASSED tests/test_categories.py::test_delete_category_not_found
PASSED tests/test_categories.py::test_delete_category_with_products_conflict
9 passed
```

- [ ] **Step 8: Run full suite — no regressions**

```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend/tests/conftest.py backend/app/services/category_service.py backend/app/routers/categories.py backend/tests/test_categories.py backend/app/main.py
git commit -m "feat(catalog): add Category CRUD (service + router + tests)"
```

---

## Task 4: Product Service + Tests (TDD)

**Files:**
- Create: `backend/app/services/product_service.py`
- Create: `backend/tests/test_products.py`

- [ ] **Step 1: Write failing tests in `backend/tests/test_products.py`**

```python
def test_list_products_authenticated(client, admin_headers):
    resp = client.get("/products", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_products_unauthenticated(client):
    resp = client.get("/products")
    assert resp.status_code == 401


def test_create_product_admin(client, admin_headers):
    resp = client.post(
        "/products",
        json={"nombre": "Coca-Cola", "precio": "1.50", "stock": 10, "stock_minimo": 2},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "Coca-Cola"
    assert data["stock"] == 10
    assert data["stock_minimo"] == 2
    assert "id" in data


def test_create_product_invalid_price(client, admin_headers):
    resp = client.post(
        "/products",
        json={"nombre": "X", "precio": "0"},
        headers=admin_headers,
    )
    assert resp.status_code == 422


def test_create_product_cashier_forbidden(client, cashier_headers):
    resp = client.post(
        "/products",
        json={"nombre": "X", "precio": "1.00"},
        headers=cashier_headers,
    )
    assert resp.status_code == 403


def test_get_product(client, admin_headers):
    create = client.post(
        "/products", json={"nombre": "Fanta", "precio": "1.20"}, headers=admin_headers
    )
    prod_id = create.json()["id"]
    resp = client.get(f"/products/{prod_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Fanta"


def test_get_product_not_found(client, admin_headers):
    resp = client.get("/products/9999", headers=admin_headers)
    assert resp.status_code == 404


def test_update_product_admin(client, admin_headers):
    create = client.post(
        "/products", json={"nombre": "Agua", "precio": "0.80"}, headers=admin_headers
    )
    prod_id = create.json()["id"]
    resp = client.put(
        f"/products/{prod_id}", json={"precio": "1.00"}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["precio"] == "1.00"


def test_update_product_cashier_forbidden(client, cashier_headers, admin_headers):
    create = client.post(
        "/products", json={"nombre": "Zumo", "precio": "1.50"}, headers=admin_headers
    )
    prod_id = create.json()["id"]
    resp = client.put(
        f"/products/{prod_id}", json={"precio": "2.00"}, headers=cashier_headers
    )
    assert resp.status_code == 403


def test_update_product_not_found(client, admin_headers):
    resp = client.put(
        "/products/9999", json={"nombre": "X"}, headers=admin_headers
    )
    assert resp.status_code == 404


def test_delete_product_admin(client, admin_headers):
    create = client.post(
        "/products", json={"nombre": "Borrable", "precio": "0.50"}, headers=admin_headers
    )
    prod_id = create.json()["id"]
    resp = client.delete(f"/products/{prod_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_delete_product_not_found(client, admin_headers):
    resp = client.delete("/products/9999", headers=admin_headers)
    assert resp.status_code == 404


def test_filter_products_by_category(client, admin_headers):
    cat = client.post(
        "/categories", json={"nombre": "Refrescos"}, headers=admin_headers
    ).json()
    client.post(
        "/products",
        json={"nombre": "Pepsi", "precio": "1.50", "category_id": cat["id"]},
        headers=admin_headers,
    )
    client.post(
        "/products",
        json={"nombre": "Agua Sin Cat", "precio": "0.80"},
        headers=admin_headers,
    )
    resp = client.get(f"/products?category_id={cat['id']}", headers=admin_headers)
    assert resp.status_code == 200
    names = [p["nombre"] for p in resp.json()]
    assert "Pepsi" in names
    assert "Agua Sin Cat" not in names


def test_product_includes_category(client, admin_headers):
    cat = client.post(
        "/categories", json={"nombre": "Lácteos"}, headers=admin_headers
    ).json()
    create = client.post(
        "/products",
        json={"nombre": "Leche", "precio": "1.20", "category_id": cat["id"]},
        headers=admin_headers,
    )
    data = create.json()
    assert data["category"]["nombre"] == "Lácteos"
```

- [ ] **Step 2: Run tests — expect FAIL (404, router not registered)**

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_products.py -v
```

Expected: all tests fail with 404.

- [ ] **Step 3: Create `backend/app/services/product_service.py`**

```python
from sqlalchemy.orm import Session

from app.models.product import Product


def get_all_products(db: Session, category_id: int | None = None) -> list[Product]:
    q = db.query(Product)
    if category_id is not None:
        q = q.filter(Product.category_id == category_id)
    return q.order_by(Product.nombre).all()


def get_product(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def create_product(db: Session, **kwargs) -> Product:
    product = Product(**kwargs)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: dict) -> Product | None:
    product = get_product(db, product_id)
    if product is None:
        return None
    for key, value in data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = get_product(db, product_id)
    if product is None:
        return False
    db.delete(product)
    db.commit()
    return True
```

- [ ] **Step 4: Create `backend/app/routers/products.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    category_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return product_service.get_all_products(db, category_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return product_service.create_product(db, **payload.model_dump())


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = product_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = product_service.update_product(
        db, product_id, payload.model_dump(exclude_unset=True)
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    found = product_service.delete_product(db, product_id)
    if not found:
        raise HTTPException(status_code=404, detail="Product not found")
```

- [ ] **Step 5: Register the products router in `backend/app/main.py`**

Replace the entire file:

```python
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine, Base
import app.models  # noqa: F401
from app.routers import auth, categories, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY == "change-me-in-production":
        warnings.warn(
            "SECRET_KEY is using the insecure default value. "
            "Set the SECRET_KEY environment variable before deploying to production.",
            stacklevel=2,
        )
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="TPV Automation", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run product tests — expect all PASS**

```bash
cd backend
.venv/Scripts/python -m pytest tests/test_products.py -v
```

Expected:
```
PASSED tests/test_products.py::test_list_products_authenticated
PASSED tests/test_products.py::test_list_products_unauthenticated
PASSED tests/test_products.py::test_create_product_admin
PASSED tests/test_products.py::test_create_product_invalid_price
PASSED tests/test_products.py::test_create_product_cashier_forbidden
PASSED tests/test_products.py::test_get_product
PASSED tests/test_products.py::test_get_product_not_found
PASSED tests/test_products.py::test_update_product_admin
PASSED tests/test_products.py::test_update_product_cashier_forbidden
PASSED tests/test_products.py::test_update_product_not_found
PASSED tests/test_products.py::test_delete_product_admin
PASSED tests/test_products.py::test_delete_product_not_found
PASSED tests/test_products.py::test_filter_products_by_category
PASSED tests/test_products.py::test_product_includes_category
14 passed
```

- [ ] **Step 7: Run full suite — no regressions**

```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/product_service.py backend/app/routers/products.py backend/tests/test_products.py backend/app/main.py
git commit -m "feat(catalog): add Product CRUD (service + router + tests)"
```

---

## Task 5: Frontend Setup

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Install frontend dependencies**

```bash
cd frontend
npm install react-router-dom@^7 zustand@^5 @tanstack/react-query@^5
```

- [ ] **Step 2: Fix the Vite proxy to strip the `/api` prefix**

Replace `frontend/vite.config.ts` with:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

With this config, a frontend call to `/api/products` is forwarded to `http://localhost:8000/products`.

- [ ] **Step 3: Commit**

```bash
cd frontend
git add vite.config.ts package.json package-lock.json
git commit -m "feat(catalog): install react-router-dom, zustand, react-query; fix vite proxy rewrite"
```

---

## Task 6: API Client Layer

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/api/categories.ts`
- Create: `frontend/src/api/products.ts`

- [ ] **Step 1: Create `frontend/src/api/client.ts`**

```ts
import { useAuthStore } from '../store/authStore'

const BASE = '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().token
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    useAuthStore.getState().logout()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (res.status === 204) return null as T

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw error
  }

  return res.json()
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
}
```

- [ ] **Step 2: Create `frontend/src/api/auth.ts`**

```ts
import { apiClient } from './client'

export interface UserInfo {
  id: number
  username: string
  role: 'admin' | 'cashier'
}

interface LoginResponse {
  access_token: string
  token_type: string
}

export async function getMe(token: string): Promise<UserInfo> {
  const res = await fetch('/api/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })
  if (!res.ok) throw new Error('Failed to get user')
  return res.json()
}

export async function login(
  username: string,
  password: string,
): Promise<{ token: string; user: UserInfo }> {
  const { access_token } = await apiClient.post<LoginResponse>('/auth/login', {
    username,
    password,
  })
  const user = await getMe(access_token)
  return { token: access_token, user }
}
```

- [ ] **Step 3: Create `frontend/src/api/categories.ts`**

```ts
import { apiClient } from './client'

export interface CategoryOut {
  id: number
  nombre: string
}

export const getCategories = () => apiClient.get<CategoryOut[]>('/categories')

export const createCategory = (nombre: string) =>
  apiClient.post<CategoryOut>('/categories', { nombre })

export const updateCategory = (id: number, nombre: string) =>
  apiClient.put<CategoryOut>(`/categories/${id}`, { nombre })

export const deleteCategory = (id: number) => apiClient.delete(`/categories/${id}`)
```

- [ ] **Step 4: Create `frontend/src/api/products.ts`**

```ts
import { apiClient } from './client'
import type { CategoryOut } from './categories'

export interface ProductOut {
  id: number
  nombre: string
  precio: string
  stock: number
  stock_minimo: number
  category_id: number | null
  category: CategoryOut | null
}

export interface ProductCreate {
  nombre: string
  precio: string
  stock?: number
  stock_minimo?: number
  category_id?: number | null
}

export interface ProductUpdate {
  nombre?: string
  precio?: string
  stock?: number
  stock_minimo?: number
  category_id?: number | null
}

export const getProducts = (category_id?: number) =>
  apiClient.get<ProductOut[]>(
    category_id != null ? `/products?category_id=${category_id}` : '/products',
  )

export const getProduct = (id: number) => apiClient.get<ProductOut>(`/products/${id}`)

export const createProduct = (data: ProductCreate) =>
  apiClient.post<ProductOut>('/products', data)

export const updateProduct = (id: number, data: ProductUpdate) =>
  apiClient.put<ProductOut>(`/products/${id}`, data)

export const deleteProduct = (id: number) => apiClient.delete(`/products/${id}`)
```

- [ ] **Step 5: Verify TypeScript compiles with no errors**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors. (There may be warnings about missing imports from App.tsx — those resolve in Task 7.)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/
git commit -m "feat(catalog): add API client layer (client, auth, products, categories)"
```

---

## Task 7: Auth Store

**Files:**
- Create: `frontend/src/store/authStore.ts`

- [ ] **Step 1: Create `frontend/src/store/authStore.ts`**

```ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserInfo } from '../api/auth'

interface AuthState {
  token: string | null
  user: UserInfo | null
  setAuth: (token: string, user: UserInfo) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' },
  ),
)
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors related to authStore.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/authStore.ts
git commit -m "feat(catalog): add Zustand auth store with localStorage persistence"
```

---

## Task 8: App Shell (Routing + Layout + Sidebar)

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/components/Sidebar.tsx`

- [ ] **Step 1: Create `frontend/src/components/ProtectedRoute.tsx`**

```tsx
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute() {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <Outlet />
}
```

- [ ] **Step 2: Create `frontend/src/components/Layout.tsx`**

```tsx
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/Sidebar.tsx`**

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

        <div className="relative group">
          <button
            disabled
            className="w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium text-gray-400 cursor-not-allowed"
          >
            Ventas
          </button>
          <span className="absolute left-full ml-2 top-1/2 -translate-y-1/2 hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
            Próximamente
          </span>
        </div>
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

- [ ] **Step 4: Replace `frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import CatalogPage from './pages/CatalogPage'

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
              <Route
                path="/ventas"
                element={
                  <div className="flex items-center justify-center h-64 text-gray-400">
                    Ventas — Próximamente
                  </div>
                }
              />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

Note: `LoginPage` and `CatalogPage` don't exist yet — TypeScript will error until Task 9 and 11 are done. Create empty placeholder files now to unblock compilation:

`frontend/src/pages/LoginPage.tsx`:
```tsx
export default function LoginPage() {
  return <div>Login</div>
}
```

`frontend/src/pages/CatalogPage.tsx`:
```tsx
export default function CatalogPage() {
  return <div>Catálogo</div>
}
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/ProtectedRoute.tsx frontend/src/components/Layout.tsx frontend/src/components/Sidebar.tsx frontend/src/pages/LoginPage.tsx frontend/src/pages/CatalogPage.tsx
git commit -m "feat(catalog): add app shell (routing, ProtectedRoute, Layout, Sidebar)"
```

---

## Task 9: Login Page

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/LoginPage.tsx`**

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { token, user } = await login(username, password)
      setAuth(token, user)
      navigate('/catalogo')
    } catch {
      setError('Usuario o contraseña incorrectos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-indigo-600 text-center mb-6">TPV</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Usuario
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/LoginPage.tsx
git commit -m "feat(catalog): add LoginPage"
```

---

## Task 10: ProductCard + ProductFormModal

**Files:**
- Create: `frontend/src/components/ProductCard.tsx`
- Create: `frontend/src/components/ProductFormModal.tsx`

- [ ] **Step 1: Create `frontend/src/components/ProductCard.tsx`**

```tsx
import type { ProductOut } from '../api/products'

interface Props {
  product: ProductOut
  isAdmin: boolean
  onEdit: () => void
  onDelete: () => void
}

export default function ProductCard({ product, isAdmin, onEdit, onDelete }: Props) {
  const stockOk = product.stock >= product.stock_minimo

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
      {/* Image placeholder */}
      <div className="aspect-square bg-gray-50 flex items-center justify-center relative">
        <svg
          className="w-12 h-12 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
          />
        </svg>

        {isAdmin && (
          <div className="absolute top-2 right-2 flex gap-1">
            <button
              onClick={onEdit}
              className="p-1.5 bg-white rounded-lg shadow-sm hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 transition-colors"
              title="Editar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                />
              </svg>
            </button>
            <button
              onClick={onDelete}
              className="p-1.5 bg-white rounded-lg shadow-sm hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
              title="Eliminar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3 flex flex-col gap-1 flex-1">
        <p className="font-semibold text-gray-900 text-sm truncate">{product.nombre}</p>
        {product.category && (
          <span className="inline-block w-fit text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">
            {product.category.nombre}
          </span>
        )}
        <div className="mt-auto pt-2 flex items-center justify-between">
          <span className="text-base font-bold text-gray-900">
            {parseFloat(product.precio).toFixed(2)} €
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              stockOk ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'
            }`}
          >
            {product.stock} uds
          </span>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/ProductFormModal.tsx`**

```tsx
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
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ProductCard.tsx frontend/src/components/ProductFormModal.tsx
git commit -m "feat(catalog): add ProductCard and ProductFormModal components"
```

---

## Task 11: Catalog Page

**Files:**
- Modify: `frontend/src/pages/CatalogPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/CatalogPage.tsx`**

```tsx
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

  const queryClient = useQueryClient()

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const { data: products = [], isLoading } = useQuery({
    queryKey: ['products', categoryFilter],
    queryFn: () =>
      getProducts(categoryFilter ? Number(categoryFilter) : undefined),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteProduct(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
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
      deleteMutation.mutate(id)
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
        >
          +
        </button>
      )}

      {/* Modal */}
      {modalOpen && (
        <ProductFormModal
          product={editingProduct}
          categories={categories}
          onClose={handleModalClose}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/CatalogPage.tsx
git commit -m "feat(catalog): add CatalogPage with card grid, filters, and admin FAB"
```

---

## Task 12: End-to-End Smoke Test

- [ ] **Step 1: Start the backend**

```bash
cd backend
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Seed the admin user (in a second terminal)**

```bash
cd backend
.venv/Scripts/python -m scripts.seed_admin
```

Expected output: `[seed] Created admin user 'admin' (role=admin).`

- [ ] **Step 3: Start the frontend**

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in the browser.

- [ ] **Step 4: Test golden paths**

1. Browser redirects to `/login` — verify login card appears
2. Enter wrong credentials → error "Usuario o contraseña incorrectos" appears
3. Enter `admin` / `admin1234` → redirects to `/catalogo`
4. Sidebar shows "TPV" logo, "Catálogo" active link, "Ventas" disabled
5. Bottom of sidebar shows "ad" avatar + "admin" username
6. Grid is empty — "No hay productos" state shows
7. FAB "+" button is visible (admin user)
8. Click "+" → modal "Nuevo producto" opens
9. Create a product: nombre="Coca-Cola", precio=1.50, stock=10, stock_minimo=2
10. Modal closes, card appears in grid
11. Card shows: name, price "1.50 €", stock chip green "10 uds"
12. Click pencil icon → modal "Editar producto" opens prefilled
13. Change precio to 2.00, save → card updates
14. Click trash icon → confirm dialog → card disappears
15. Click "Cerrar sesión" → redirects to `/login`
16. Verify refreshing `/catalogo` while logged out → redirects to `/login`

- [ ] **Step 5: Final commit and push**

```bash
git add .
git commit -m "feat(phase3): complete catalog UI smoke test"
git push origin main
```

---

## Spec Coverage Check

| Spec requirement | Task |
|-----------------|------|
| GET /categories (authenticated) | Task 3 |
| POST /categories (admin only) | Task 3 |
| PUT /categories/{id} (admin only) | Task 3 |
| DELETE /categories/{id} — 409 if has products | Task 3 |
| GET /products with ?category_id filter | Task 4 |
| POST /products (admin only) | Task 4 |
| GET /products/{id} | Task 4 |
| PUT /products/{id} (partial update) | Task 4 |
| DELETE /products/{id} | Task 4 |
| require_admin dependency | Task 2 |
| Pydantic schemas (CategoryOut, ProductOut with nested category) | Task 1 |
| precio > 0 validator | Task 1 |
| Vite proxy /api → backend (strip prefix) | Task 5 |
| Zustand auth store (token + user, localStorage) | Task 7 |
| ProtectedRoute redirect to /login | Task 8 |
| Sidebar with disabled Ventas link | Task 8 |
| LoginPage with inline error | Task 9 |
| ProductCard with isAdmin controls | Task 10 |
| ProductFormModal (create + edit, shared) | Task 10 |
| CatalogPage grid 2→3→4 cols | Task 11 |
| Category filter (server-side) | Task 11 |
| Name search (client-side) | Task 11 |
| Admin FAB to create product | Task 11 |
| Empty state | Task 11 |
| React Query invalidation after mutations | Task 11 |
