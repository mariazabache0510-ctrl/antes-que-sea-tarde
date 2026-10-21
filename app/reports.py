from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.risk import EN_RIESGO

BOGOTA = ZoneInfo("America/Bogota")
_MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
_NIVEL_COLOR = {
    "Medio": colors.HexColor("#8a5a12"),
    "Alto": colors.HexColor("#9a3412"),
    "Crítico": colors.HexColor("#9f1239"),
}


def build_pdf(students) -> bytes:
    ordered = sorted(
        (student for student in students if student.risk_level in EN_RIESGO),
        key=lambda student: (-student.risk_score, student.nombre),
    )
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title="Estudiantes en riesgo",
        author="Antes que sea tarde",
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=48,
        pageCompression=0,
    )
    styles = _styles()
    story = [
        Paragraph("Antes que sea tarde", styles["kicker"]),
        Paragraph("Estudiantes en riesgo", styles["title"]),
        Paragraph(_fecha(), styles["meta"]),
        Spacer(1, 8),
        Paragraph(
            "Listado para Permanencia y docentes MAIE. La acción sugerida orienta el acompañamiento; "
            "no reemplaza el criterio del docente.",
            styles["body"],
        ),
        Spacer(1, 12),
    ]
    if not ordered:
        story.append(Paragraph("No hay estudiantes en riesgo con la carga actual.", styles["body"]))
    else:
        story.append(Paragraph(f"{len(ordered)} estudiantes para acompañar, de mayor a menor puntaje.", styles["body"]))
        story.append(Spacer(1, 10))
        story.append(_table(ordered, styles))
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _fecha() -> str:
    moment = datetime.now(BOGOTA)
    return f"{moment.day} de {_MESES[moment.month - 1]} de {moment.year}, {moment:%H:%M} (hora Colombia)"


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "kicker": ParagraphStyle(
            "kicker",
            fontName="Times-Bold",
            fontSize=9,
            textColor=colors.HexColor("#1b4332"),
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Times-Bold",
            fontSize=20,
            textColor=colors.HexColor("#1c1915"),
            leading=24,
            spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Times-Italic",
            fontSize=9,
            textColor=colors.HexColor("#6b6258"),
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Times-Roman",
            fontSize=10,
            textColor=colors.HexColor("#1c1915"),
            leading=14,
        ),
        "head": ParagraphStyle(
            "head",
            fontName="Times-Bold",
            fontSize=8,
            textColor=colors.white,
            leading=10,
        ),
        "cell": ParagraphStyle(
            "cell",
            fontName="Times-Roman",
            fontSize=8,
            textColor=colors.HexColor("#1c1915"),
            leading=10,
        ),
    }


def _table(students, styles) -> Table:
    header = [
        Paragraph(pdf_safe(label), styles["head"])
        for label in ("Documento", "Nombre", "Programa", "Sem.", "Prom.", "Nivel", "Pts.", "Acción sugerida")
    ]
    data = [header]
    for student in students:
        level_style = ParagraphStyle(
            f"nivel-{student.risk_level}",
            parent=styles["cell"],
            textColor=_NIVEL_COLOR.get(student.risk_level, colors.black),
            fontName="Times-Bold",
        )
        data.append(
            [
                Paragraph(pdf_safe(student.documento), styles["cell"]),
                Paragraph(pdf_safe(student.nombre), styles["cell"]),
                Paragraph(pdf_safe(student.programa), styles["cell"]),
                Paragraph(str(student.semestre), styles["cell"]),
                Paragraph(f"{float(student.promedio):.2f}", styles["cell"]),
                Paragraph(pdf_safe(student.risk_level), level_style),
                Paragraph(str(student.risk_score), styles["cell"]),
                Paragraph(pdf_safe(student.accion), styles["cell"]),
            ]
        )
    table = Table(
        data,
        colWidths=[62, 78, 88, 28, 34, 42, 28, 123],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b4332")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fffcf7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fffcf7"), colors.HexColor("#f6f1e7")]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e4d9c8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _footer(canvas, _doc) -> None:
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#6b6258"))
    canvas.setFont("Times-Italic", 8)
    canvas.drawString(
        36,
        28,
        "Antes que sea tarde. Datos académicos usados solo para priorizar el acompañamiento.",
    )
    canvas.restoreState()


def pdf_safe(value) -> str:
    cleaned = str(value).encode("latin-1", "replace").decode("latin-1")
    return escape(cleaned)
