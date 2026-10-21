"""Write the sample workbook the jury can download from the app."""

from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "sample" / "estudiantes_ejemplo.xlsx"

HEADERS = [
    "documento",
    "nombre",
    "programa",
    "semestre",
    "promedio",
    "materias_perdidas",
    "inasistencias",
    "evaluaciones_no_presentadas",
]

ROWS = [
    ["10001001", "Camila Ríos", "Tecnología en Desarrollo de Software", 4, 4.3, 0, 0, 0],
    ["10001002", "Mateo López", "Licenciatura en Educación Infantil", 6, 3.8, 0, 1, 0],
    ["10001003", "Sara Gómez", "Tecnología en Desarrollo de Software", 1, 3.2, 1, 2, 0],
    ["10001004", "Julián Peña", "Licenciatura en Educación Infantil", 3, 2.6, 2, 3, 1],
    ["10001005", "Valentina Cruz", "Tecnología en Desarrollo de Software", 2, 1.8, 3, 6, 2],
    ["10001006", "Andrés Molina", "Licenciatura en Educación Infantil", 1, 2.2, 2, 5, 1],
    ["10001007", "Laura Méndez", "Tecnología en Desarrollo de Software", 1, 1.2, 4, 8, 3],
    ["10001008", "Diego Salazar", "Licenciatura en Educación Infantil", 2, 0.8, 4, 7, 3],
]


def main() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Estudiantes"
    sheet.append(HEADERS)
    for row in ROWS:
        sheet.append(row)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(DESTINATION)
    print(DESTINATION)


if __name__ == "__main__":
    main()
