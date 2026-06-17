from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_admin
from app.schemas.shift import ShiftCreate, ShiftUpdate, ShiftOut
from app.services import shift_service

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.get("", response_model=list[ShiftOut])
def list_shifts(
    employee_id: Optional[int] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    return shift_service.get_shifts(db, employee_id=employee_id,
                                    fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@router.post("", response_model=ShiftOut, status_code=201)
def create_shift(data: ShiftCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return shift_service.create_shift(
        db,
        employee_id=data.employee_id,
        fecha=data.fecha,
        hora_inicio=data.hora_inicio,
        hora_fin=data.hora_fin,
    )


@router.get("/{shift_id}", response_model=ShiftOut)
def get_shift(shift_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    s = shift_service.get_shift(db, shift_id)
    if not s:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return s


@router.put("/{shift_id}", response_model=ShiftOut)
def update_shift(shift_id: int, data: ShiftUpdate,
                 db: Session = Depends(get_db), _=Depends(require_admin)):
    s = shift_service.update_shift(db, shift_id, data.model_dump(exclude_none=True))
    if not s:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return s


@router.delete("/{shift_id}", status_code=204)
def delete_shift(shift_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    s = shift_service.get_shift(db, shift_id)
    if not s:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    shift_service.delete_shift(db, shift_id)
