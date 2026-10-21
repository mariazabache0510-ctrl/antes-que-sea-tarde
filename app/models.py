from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class Student(db.Model):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("semestre >= 1 AND semestre <= 20", name="ck_student_semestre"),
        CheckConstraint("promedio >= 0 AND promedio <= 5", name="ck_student_promedio"),
        CheckConstraint(
            "materias_perdidas >= 0 AND materias_perdidas <= 40",
            name="ck_student_materias",
        ),
        CheckConstraint("inasistencias >= 0 AND inasistencias <= 200", name="ck_student_inasistencias"),
        CheckConstraint(
            "evaluaciones_no_presentadas >= 0 AND evaluaciones_no_presentadas <= 40",
            name="ck_student_evaluaciones",
        ),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="ck_student_risk"),
        CheckConstraint(
            "risk_level IN ('Bajo', 'Medio', 'Alto', 'Crítico')",
            name="ck_student_nivel",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    documento: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    programa: Mapped[str] = mapped_column(String(120), nullable=False)
    semestre: Mapped[int] = mapped_column(Integer, nullable=False)
    promedio: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    materias_perdidas: Mapped[int] = mapped_column(Integer, nullable=False)
    inasistencias: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluaciones_no_presentadas: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    accion: Mapped[str] = mapped_column(String(180), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class ImportBatch(db.Model):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(120), nullable=False)
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
