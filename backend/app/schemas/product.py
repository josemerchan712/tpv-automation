from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.category import CategoryOut


class ProductCreate(BaseModel):
    nombre: str
    precio: Decimal
    stock: int = 0
    stock_minimo: int = 0
    category_id: int | None = None

    @field_validator("precio")
    @classmethod
    def precio_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("precio must be greater than 0")
        return v


class ProductUpdate(BaseModel):
    nombre: str | None = None
    precio: Decimal | None = None
    stock: int | None = None
    stock_minimo: int | None = None
    category_id: int | None = None

    @field_validator("precio")
    @classmethod
    def precio_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("precio must be greater than 0")
        return v


class ProductOut(BaseModel):
    id: int
    nombre: str
    precio: Decimal
    stock: int
    stock_minimo: int
    category_id: int | None
    category: CategoryOut | None

    model_config = {"from_attributes": True}
