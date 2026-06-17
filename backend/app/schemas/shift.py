from datetime import date, time
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, model_validator


class ShiftCreate(BaseModel):
    employee_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time

    @model_validator(mode="after")
    def end_after_start(self) -> "ShiftCreate":
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return self


class ShiftUpdate(BaseModel):
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None

    @model_validator(mode="after")
    def end_after_start(self) -> "ShiftUpdate":
        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return self


class ShiftOut(BaseModel):
    id: int
    employee_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    horas_trabajadas: Decimal

    model_config = {"from_attributes": True}


class HoursSummaryOut(BaseModel):
    employee_id: int
    nombre: str
    periodo: Literal["semana", "mes"]
    fecha_inicio: date
    fecha_fin: date
    total_horas_trabajadas: Decimal
    horas_contratadas: Decimal
    diferencia: Decimal
