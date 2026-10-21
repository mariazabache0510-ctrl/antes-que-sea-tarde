NIVELES = ("Bajo", "Medio", "Alto", "Crítico")
EN_RIESGO = frozenset({"Medio", "Alto", "Crítico"})

ACCIONES = {
    "Bajo": "Seguimiento ordinario del periodo.",
    "Medio": "Tutoría y contacto del docente MAIE esta semana.",
    "Alto": "Cita de acompañamiento y revisión de materias perdidas.",
    "Crítico": "Intervención inmediata de Permanencia Estudiantil.",
}


def nivel_y_accion(score: int) -> tuple[str, str]:
    if score <= 24:
        nivel = "Bajo"
    elif score <= 49:
        nivel = "Medio"
    elif score <= 74:
        nivel = "Alto"
    else:
        nivel = "Crítico"
    return nivel, ACCIONES[nivel]


def calcular_riesgo(
    promedio: float,
    materias_perdidas: int,
    inasistencias: int,
    evaluaciones_no_presentadas: int,
    semestre: int,
) -> tuple[int, str, str]:
    """Transparent 0–100 score. The grade below 3.0 is the largest slice.

    Promedio: up to 55 points. Below 3.0 starts at 15 and grows to 55.
    Materias perdidas: up to 18, capped at 4 subjects.
    Inasistencias: up to 15, capped at 8.
    Evaluaciones no presentadas: up to 7, capped at 3.
    Semestre 1 or 2: 5 extra points.
    """
    nota = float(promedio)
    if nota >= 4:
        puntos_promedio = 0.0
    elif nota >= 3:
        puntos_promedio = (4 - nota) * 15
    else:
        puntos_promedio = 15 + ((3 - nota) / 3) * 40

    puntos_materias = min(int(materias_perdidas), 4) / 4 * 18
    puntos_inasistencias = min(int(inasistencias), 8) / 8 * 15
    puntos_evaluaciones = min(int(evaluaciones_no_presentadas), 3) / 3 * 7
    puntos_semestre = 5 if int(semestre) <= 2 else 0

    score = round(
        puntos_promedio + puntos_materias + puntos_inasistencias + puntos_evaluaciones + puntos_semestre
    )
    score = max(0, min(100, score))
    nivel, accion = nivel_y_accion(score)
    return score, nivel, accion
