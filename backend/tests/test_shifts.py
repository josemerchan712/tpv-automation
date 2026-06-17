import pytest
from datetime import date, time
from decimal import Decimal
from app.services import shift_service, employee_service


def make_shift(db, employee_id, fecha=date(2024, 6, 10),
               hora_inicio=time(9, 0), hora_fin=time(17, 0)):
    return shift_service.create_shift(
        db, employee_id=employee_id,
        fecha=fecha, hora_inicio=hora_inicio, hora_fin=hora_fin
    )


class TestShiftService:
    def test_create_shift_computes_hours(self, db, employee):
        shift = make_shift(db, employee.id)
        assert shift.id is not None
        assert shift.horas_trabajadas == Decimal("8.00")

    def test_create_shift_partial_hours(self, db, employee):
        shift = make_shift(db, employee.id, hora_inicio=time(9, 0), hora_fin=time(13, 30))
        assert shift.horas_trabajadas == Decimal("4.50")

    def test_get_shift(self, db, employee):
        shift = make_shift(db, employee.id)
        fetched = shift_service.get_shift(db, shift.id)
        assert fetched.id == shift.id

    def test_get_shift_not_found(self, db):
        assert shift_service.get_shift(db, 9999) is None

    def test_get_shifts_no_filter(self, db, employee):
        make_shift(db, employee.id, fecha=date(2024, 6, 10))
        make_shift(db, employee.id, fecha=date(2024, 6, 11))
        shifts = shift_service.get_shifts(db)
        assert len(shifts) == 2

    def test_get_shifts_by_employee(self, db, employee):
        from app.services.employee_service import create_employee
        other = create_employee(db, nombre="Otro", puesto="X",
                                horas_semanales_contratadas=Decimal("20"),
                                fecha_alta=date(2024, 1, 1))
        make_shift(db, employee.id)
        make_shift(db, other.id)
        result = shift_service.get_shifts(db, employee_id=employee.id)
        assert len(result) == 1
        assert result[0].employee_id == employee.id

    def test_get_shifts_by_date_range(self, db, employee):
        make_shift(db, employee.id, fecha=date(2024, 6, 1))
        make_shift(db, employee.id, fecha=date(2024, 6, 15))
        make_shift(db, employee.id, fecha=date(2024, 6, 30))
        result = shift_service.get_shifts(
            db, fecha_inicio=date(2024, 6, 10), fecha_fin=date(2024, 6, 20)
        )
        assert len(result) == 1

    def test_update_shift_recomputes_hours(self, db, employee):
        shift = make_shift(db, employee.id)
        updated = shift_service.update_shift(
            db, shift.id, {"hora_fin": time(18, 0)}
        )
        assert updated.horas_trabajadas == Decimal("9.00")

    def test_delete_shift(self, db, employee):
        shift = make_shift(db, employee.id)
        shift_service.delete_shift(db, shift.id)
        assert shift_service.get_shift(db, shift.id) is None
