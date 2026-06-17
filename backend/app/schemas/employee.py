from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator


class EmployeeCreate(BaseModel):
    user_id: Optional[int] = None
    nombre: str
    puesto: str
    horas_semanales_contratadas: Decimal
    fecha_alta: date

    @field_validator("nombre", "puesto")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("No puede estar vacío")
        return v

    @field_validator("horas_semanales_contratadas")
    @classmethod
    def positive_hours(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Las horas contratadas deben ser positivas")
        return v


class EmployeeUpdate(BaseModel):
    user_id: Optional[int] = None
    nombre: Optional[str] = None
    puesto: Optional[str] = None
    horas_semanales_contratadas: Optional[Decimal] = None
    fecha_alta: Optional[date] = None


class EmployeeOut(BaseModel):
    id: int
    user_id: Optional[int]
    nombre: str
    puesto: str
    horas_semanales_contratadas: Decimal
    fecha_alta: date

    model_config = {"from_attributes": True}
