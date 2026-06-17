from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.employee import Employee


def get_all_employees(db: Session) -> list[Employee]:
    return db.query(Employee).order_by(Employee.nombre).all()


def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def create_employee(
    db: Session,
    nombre: str,
    puesto: str,
    horas_semanales_contratadas: Decimal,
    fecha_alta: date,
    user_id: Optional[int] = None,
) -> Employee:
    emp = Employee(
        nombre=nombre,
        puesto=puesto,
        horas_semanales_contratadas=horas_semanales_contratadas,
        fecha_alta=fecha_alta,
        user_id=user_id,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def update_employee(db: Session, employee_id: int, data: dict) -> Optional[Employee]:
    emp = get_employee(db, employee_id)
    if not emp:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(emp, key, value)
    db.commit()
    db.refresh(emp)
    return emp


def delete_employee(db: Session, employee_id: int) -> None:
    emp = get_employee(db, employee_id)
    if emp:
        db.delete(emp)
        db.commit()
