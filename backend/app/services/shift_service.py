from datetime import date, time, datetime
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
