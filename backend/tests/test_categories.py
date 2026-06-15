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
