def test_list_products_authenticated(client, admin_headers):
    resp = client.get("/products", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_products_unauthenticated(client):
    resp = client.get("/products")
    assert resp.status_code == 401


def test_list_products_cashier_can_read(client, cashier_headers):
    resp = client.get("/products", headers=cashier_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


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
