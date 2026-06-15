from pydantic import BaseModel
from typing import Annotated
from pydantic import StringConstraints


class CategoryCreate(BaseModel):
    nombre: Annotated[str, StringConstraints(min_length=1, max_length=100, strip_whitespace=True)]


class CategoryOut(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}
