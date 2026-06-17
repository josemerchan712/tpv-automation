from calendar import monthrange
from datetime import date, time, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy.orm import Session
from app.models.employee import Shift


def _compute_hours(hora_inicio: time, hora_fin: time) -> Decimal:
    base_date = datetime(2000, 1, 1)
    delta = datetime.combine(base_date.date(), hora_fin) - datetime.combine(base_date.date(), hora_inicio)
    hours = Decimal(str(delta.seconds / 3600)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return hours


def get_shifts(
    db: Session,
    employee_id: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
) -> list[Shift]:
    q = db.query(Shift)
    if employee_id is not None:
        q = q.filter(Shift.employee_id == employee_id)
    if fecha_inicio is not None:
        q = q.filter(Shift.fecha >= fecha_inicio)
    if fecha_fin is not None:
        q = q.filter(Shift.fecha <= fecha_fin)
    return q.order_by(Shift.fecha, Shift.hora_inicio).all()


def get_shift(db: Session, shift_id: int) -> Optional[Shift]:
    return db.query(Shift).filter(Shift.id == shift_id).first()


def create_shift(
    db: Session,
    employee_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
) -> Shift:
    shift = Shift(
        employee_id=employee_id,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        horas_trabajadas=_compute_hours(hora_inicio, hora_fin),
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def update_shift(db: Session, shift_id: int, data: dict) -> Optional[Shift]:
    shift = get_shift(db, shift_id)
    if not shift:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(shift, key, value)
    shift.horas_trabajadas = _compute_hours(shift.hora_inicio, shift.hora_fin)
    db.commit()
    db.refresh(shift)
    return shift


def delete_shift(db: Session, shift_id: int) -> None:
    shift = get_shift(db, shift_id)
    if shift:
        db.delete(shift)
        db.commit()


def hours_summary(db: Session, employee_id: int, periodo: str, fecha: date) -> dict:
    from app.services.employee_service import get_employee
    emp = get_employee(db, employee_id)
    if not emp:
        raise ValueError("Empleado no encontrado")

    if periodo == "semana":
        day_of_week = fecha.weekday()  # 0=Monday
        fecha_inicio = fecha - timedelta(days=day_of_week)
        fecha_fin = fecha_inicio + timedelta(days=6)
        horas_contratadas = emp.horas_semanales_contratadas
    else:  # mes
        fecha_inicio = fecha.replace(day=1)
        last_day = monthrange(fecha.year, fecha.month)[1]
        fecha_fin = fecha.replace(day=last_day)
        days = Decimal(str((fecha_fin - fecha_inicio).days + 1))
        horas_contratadas = (emp.horas_semanales_contratadas * days / Decimal("7")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    shifts = get_shifts(db, employee_id=employee_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    total = sum((s.horas_trabajadas for s in shifts), Decimal("0.00"))

    return {
        "employee_id": employee_id,
        "nombre": emp.nombre,
        "periodo": periodo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_horas_trabajadas": total,
        "horas_contratadas": horas_contratadas,
        "diferencia": total - horas_contratadas,
    }
