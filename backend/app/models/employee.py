from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nombre = Column(String, nullable=False)
    puesto = Column(String, nullable=False)
    horas_semanales_contratadas = Column(Numeric(5, 2), nullable=False)
    fecha_alta = Column(Date, nullable=False)

    user = relationship("User", backref="employee", uselist=False)
    shifts = relationship("Shift", back_populates="employee", cascade="all, delete-orphan")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    horas_trabajadas = Column(Numeric(5, 2), nullable=False)

    employee = relationship("Employee", back_populates="shifts")
