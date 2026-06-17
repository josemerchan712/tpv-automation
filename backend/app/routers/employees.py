from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_admin
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut
from app.schemas.shift import HoursSummaryOut
from app.services import employee_service, shift_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.get_all_employees(db)


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.create_employee(
        db,
        nombre=data.nombre,
        puesto=data.puesto,
        horas_semanales_contratadas=data.horas_semanales_contratadas,
        fecha_alta=data.fecha_alta,
        user_id=data.user_id,
    )


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    emp = employee_service.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return emp


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, data: EmployeeUpdate,
                    db: Session = Depends(get_db), _=Depends(require_admin)):
    emp = employee_service.update_employee(db, employee_id, data.model_dump(exclude_none=True))
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return emp


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    emp = employee_service.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    employee_service.delete_employee(db, employee_id)


@router.get("/{employee_id}/hours-summary", response_model=HoursSummaryOut)
def get_hours_summary(
    employee_id: int,
    periodo: Literal["semana", "mes"] = Query(...),
    fecha: date = Query(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    try:
        summary = shift_service.hours_summary(db, employee_id, periodo, fecha)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return summary
