from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.extensions import db
from app.models import ImportBatch, Student, utcnow
from app.risk import calcular_riesgo


class ImportPersistError(Exception):
    """The batch was rolled back. No student row was changed."""


def guardar_carga(rows: list[dict], user_id: int, filename: str) -> tuple[int, int]:
    now = utcnow()
    documentos = [row["documento"] for row in rows]
    try:
        existentes = set(
            db.session.scalars(select(Student.documento).where(Student.documento.in_(documentos))).all()
        )
        values = [_student_values(row, now) for row in rows]
        statement = pg_insert(Student).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=["documento"],
            set_={
                "nombre": statement.excluded.nombre,
                "programa": statement.excluded.programa,
                "semestre": statement.excluded.semestre,
                "promedio": statement.excluded.promedio,
                "materias_perdidas": statement.excluded.materias_perdidas,
                "inasistencias": statement.excluded.inasistencias,
                "evaluaciones_no_presentadas": statement.excluded.evaluaciones_no_presentadas,
                "risk_score": statement.excluded.risk_score,
                "risk_level": statement.excluded.risk_level,
                "accion": statement.excluded.accion,
                "updated_at": statement.excluded.updated_at,
            },
        )
        db.session.execute(statement)
        db.session.add(
            ImportBatch(
                user_id=user_id,
                filename=filename[:120] or "carga.xlsx",
                inserted_count=len(documentos) - len(existentes),
                updated_count=len(existentes),
            )
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise ImportPersistError from exc
    return len(documentos) - len(existentes), len(existentes)


def _student_values(row: dict, now) -> dict:
    score, nivel, accion = calcular_riesgo(
        row["promedio"],
        row["materias_perdidas"],
        row["inasistencias"],
        row["evaluaciones_no_presentadas"],
        row["semestre"],
    )
    promedio = row["promedio"]
    if not isinstance(promedio, Decimal):
        promedio = Decimal(f"{float(promedio):.2f}")
    return {
        "documento": row["documento"],
        "nombre": row["nombre"],
        "programa": row["programa"],
        "semestre": row["semestre"],
        "promedio": promedio,
        "materias_perdidas": row["materias_perdidas"],
        "inasistencias": row["inasistencias"],
        "evaluaciones_no_presentadas": row["evaluaciones_no_presentadas"],
        "risk_score": score,
        "risk_level": nivel,
        "accion": accion,
        "created_at": now,
        "updated_at": now,
    }
