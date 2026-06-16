from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator
from app.models.sale import PaymentMethod


class SaleItemCreate(BaseModel):
    product_id: int
    cantidad: int

    @field_validator("cantidad")
    @classmethod
    def cantidad_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("cantidad must be greater than 0")
        return v


class SaleCreate(BaseModel):
    metodo_pago: PaymentMethod
    items: list[SaleItemCreate]

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("items cannot be empty")
        return v


class SaleItemOut(BaseModel):
    id: int
    product_id: int
    cantidad: int
    precio_unitario: Decimal

    model_config = {"from_attributes": True}


class SaleOut(BaseModel):
    id: int
    fecha: datetime
    total: Decimal
    metodo_pago: PaymentMethod
    user_id: int
    items: list[SaleItemOut]

    model_config = {"from_attributes": True}


class SaleListOut(BaseModel):
    id: int
    fecha: datetime
    total: Decimal
    metodo_pago: PaymentMethod
    user_id: int

    model_config = {"from_attributes": True}
