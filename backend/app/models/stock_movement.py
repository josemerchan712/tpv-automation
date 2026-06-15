import enum
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class MovementType(str, enum.Enum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    tipo = Column(Enum(MovementType), nullable=False)
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    motivo = Column(String, nullable=True)

    product = relationship("Product", back_populates="stock_movements")
