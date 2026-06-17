import pytest
from datetime import date
from decimal import Decimal
from app.services import employee_service
from app.models.employee import Employee


def make_employee(db, nombre="Ana García", puesto="Cajera",
                  horas=Decimal("40.00"), fecha_alta=date(2024, 1, 15)):
    return employee_service.create_employee(
        db, nombre=nombre, puesto=puesto,
        horas_semanales_contratadas=horas, fecha_alta=fecha_alta
    )


class TestEmployeeService:
    def test_create_employee(self, db):
        emp = make_employee(db)
        assert emp.id is not None
        assert emp.nombre == "Ana García"
        assert emp.puesto == "Cajera"
        assert emp.horas_semanales_contratadas == Decimal("40.00")
        assert emp.fecha_alta == date(2024, 1, 15)

    def test_get_employee(self, db):
        emp = make_employee(db)
        fetched = employee_service.get_employee(db, emp.id)
        assert fetched.id == emp.id

    def test_get_employee_not_found(self, db):
        assert employee_service.get_employee(db, 9999) is None

    def test_get_all_employees(self, db):
        make_employee(db, nombre="Ana")
        make_employee(db, nombre="Carlos")
        employees = employee_service.get_all_employees(db)
        assert len(employees) == 2

    def test_update_employee(self, db):
        emp = make_employee(db)
        updated = employee_service.update_employee(db, emp.id, {"puesto": "Supervisor"})
        assert updated.puesto == "Supervisor"
        assert updated.nombre == "Ana García"

    def test_delete_employee(self, db):
        emp = make_employee(db)
        employee_service.delete_employee(db, emp.id)
        assert employee_service.get_employee(db, emp.id) is None


class TestEmployeesEndpoints:
    BASE = "/employees"

    def test_create_employee_admin(self, client, admin_headers):
        res = client.post(self.BASE, json={
            "nombre": "Carlos López",
            "puesto": "Supervisor",
            "horas_semanales_contratadas": "40.00",
            "fecha_alta": "2024-01-15",
        }, headers=admin_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["nombre"] == "Carlos López"
        assert data["puesto"] == "Supervisor"
        assert data["id"] is not None

    def test_create_employee_cashier_forbidden(self, client, cashier_headers):
        res = client.post(self.BASE, json={
            "nombre": "X", "puesto": "Y",
            "horas_semanales_contratadas": "20",
            "fecha_alta": "2024-01-01",
        }, headers=cashier_headers)
        assert res.status_code == 403

    def test_list_employees(self, client, admin_headers, employee):
        res = client.get(self.BASE, headers=admin_headers)
        assert res.status_code == 200
        assert any(e["id"] == employee.id for e in res.json())

    def test_get_employee(self, client, admin_headers, employee):
        res = client.get(f"{self.BASE}/{employee.id}", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["id"] == employee.id

    def test_get_employee_not_found(self, client, admin_headers):
        res = client.get(f"{self.BASE}/9999", headers=admin_headers)
        assert res.status_code == 404

    def test_update_employee(self, client, admin_headers, employee):
        res = client.put(f"{self.BASE}/{employee.id}",
                         json={"puesto": "Encargado"},
                         headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["puesto"] == "Encargado"

    def test_delete_employee(self, client, admin_headers, employee):
        res = client.delete(f"{self.BASE}/{employee.id}", headers=admin_headers)
        assert res.status_code == 204
        res2 = client.get(f"{self.BASE}/{employee.id}", headers=admin_headers)
        assert res2.status_code == 404

    def test_hours_summary_weekly(self, client, admin_headers, employee):
        res = client.get(
            f"{self.BASE}/{employee.id}/hours-summary",
            params={"periodo": "semana", "fecha": "2024-06-12"},
            headers=admin_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["periodo"] == "semana"
        assert data["employee_id"] == employee.id
        assert "total_horas_trabajadas" in data
        assert "horas_contratadas" in data
        assert "diferencia" in data

    def test_hours_summary_monthly(self, client, admin_headers, employee):
        res = client.get(
            f"{self.BASE}/{employee.id}/hours-summary",
            params={"periodo": "mes", "fecha": "2024-06-01"},
            headers=admin_headers,
        )
        assert res.status_code == 200

    def test_hours_summary_invalid_periodo(self, client, admin_headers, employee):
        res = client.get(
            f"{self.BASE}/{employee.id}/hours-summary",
            params={"periodo": "anio", "fecha": "2024-06-01"},
            headers=admin_headers,
        )
        assert res.status_code == 422
