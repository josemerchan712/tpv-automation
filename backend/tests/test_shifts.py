import pytest
from datetime import date, time
from decimal import Decimal, ROUND_HALF_UP
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


class TestHoursSummary:
    def test_weekly_summary_exact(self, db, employee):
        # employee has 40h/week contracted
        # Week of 2024-06-10 (Monday) to 2024-06-16 (Sunday)
        make_shift(db, employee.id, fecha=date(2024, 6, 10))  # 8h
        make_shift(db, employee.id, fecha=date(2024, 6, 11))  # 8h
        summary = shift_service.hours_summary(db, employee.id, "semana", date(2024, 6, 12))
        assert summary["periodo"] == "semana"
        assert summary["fecha_inicio"] == date(2024, 6, 10)
        assert summary["fecha_fin"] == date(2024, 6, 16)
        assert summary["total_horas_trabajadas"] == Decimal("16.00")
        assert summary["horas_contratadas"] == Decimal("40.00")
        assert summary["diferencia"] == Decimal("-24.00")

    def test_weekly_summary_over_hours(self, db, employee):
        for d in [10, 11, 12, 13, 14, 15]:
            make_shift(db, employee.id, fecha=date(2024, 6, d))  # 6 × 8h = 48h
        summary = shift_service.hours_summary(db, employee.id, "semana", date(2024, 6, 10))
        assert summary["diferencia"] == Decimal("8.00")

    def test_monthly_summary(self, db, employee):
        make_shift(db, employee.id, fecha=date(2024, 6, 10))   # 8h
        make_shift(db, employee.id, fecha=date(2024, 6, 20))   # 8h
        summary = shift_service.hours_summary(db, employee.id, "mes", date(2024, 6, 15))
        assert summary["fecha_inicio"] == date(2024, 6, 1)
        assert summary["fecha_fin"] == date(2024, 6, 30)
        assert summary["total_horas_trabajadas"] == Decimal("16.00")
        expected_contracted = (Decimal("40.00") * Decimal("30") / Decimal("7")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        assert summary["horas_contratadas"] == expected_contracted

    def test_summary_employee_not_found(self, db):
        with pytest.raises(ValueError, match="Empleado no encontrado"):
            shift_service.hours_summary(db, 9999, "semana", date(2024, 6, 10))
