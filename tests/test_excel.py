import zipfile
from io import BytesIO

from openpyxl import Workbook

from app.excel_import import parse_xlsx

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


def workbook_bytes(rows, headers=None):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers or HEADERS)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def valid_row(**changes):
    row = ["10001001", "Ana Nia", "Tecnologia", 4, 4.2, 0, 0, 0]
    for key, value in changes.items():
        row[HEADERS.index(key)] = value
    return row


def test_acepta_encabezados_con_espacios_y_coma_decimal():
    payload = workbook_bytes(
        [["10001001", "Ana Nia", "Tecnologia", "2", "3,4", 0, 0, 0]],
        headers=[
            "Documento",
            "Nombre",
            "Programa",
            "Semestre",
            "Promedio",
            "Materias perdidas",
            "Inasistencias",
            "Evaluaciones no presentadas",
        ],
    )
    rows, errors = parse_xlsx(payload)
    assert errors == []
    assert rows[0]["promedio"] == __import__("decimal").Decimal("3.40")
    assert rows[0]["semestre"] == 2


def test_rechaza_columna_faltante_celda_vacia_texto_y_promedio_fuera_de_rango():
    missing, missing_errors = parse_xlsx(workbook_bytes([valid_row()], headers=HEADERS[:-1] + ["otra"]))
    assert missing == []
    assert any("evaluaciones_no_presentadas" in error for error in missing_errors)

    empty, empty_errors = parse_xlsx(workbook_bytes([valid_row(nombre="")]))
    assert empty == []
    assert any("nombre está vacía" in error for error in empty_errors)

    text, text_errors = parse_xlsx(workbook_bytes([valid_row(promedio="alto")]))
    assert text == []
    assert any("se espera un número" in error for error in text_errors)

    high, high_errors = parse_xlsx(workbook_bytes([valid_row(promedio=6)]))
    assert high == []
    assert any("entre 0 y 5" in error for error in high_errors)


def test_rechaza_documento_repetido_en_el_mismo_archivo():
    rows, errors = parse_xlsx(workbook_bytes([valid_row(), valid_row(nombre="Otra Persona")]))
    assert rows == []
    assert any("repetido" in error for error in errors)


def test_rechaza_archivo_que_no_es_excel_o_trae_macros():
    _rows, errors = parse_xlsx(b"esto no es excel")
    assert errors == ["El archivo no es un libro de Excel válido."]

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr("xl/vbaProject.bin", "macro")
    _rows, macro_errors = parse_xlsx(buffer.getvalue())
    assert macro_errors == ["No se aceptan archivos con macros."]


def test_no_guarda_nombre_con_html():
    _rows, errors = parse_xlsx(workbook_bytes([valid_row(nombre="<script>alert(1)</script>")]))
    assert errors
    assert all("<script>" not in error for error in errors)
