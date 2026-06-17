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
