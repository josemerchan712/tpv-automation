from pydantic import BaseModel


class CategoryCreate(BaseModel):
    nombre: str


class CategoryOut(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}
