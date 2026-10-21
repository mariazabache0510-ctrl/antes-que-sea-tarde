from app.reports import build_pdf, pdf_safe


class FakeStudent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_el_pdf_trae_solo_a_quien_esta_en_riesgo():
    payload = build_pdf(
        [
            FakeStudent(
                documento="10001001",
                nombre="Camila Rios",
                programa="Tecnologia",
                semestre=4,
                promedio=4.3,
                risk_score=0,
                risk_level="Bajo",
                accion="Seguimiento ordinario del periodo.",
            ),
            FakeStudent(
                documento="10001007",
                nombre="Laura Mendez",
                programa="Tecnologia",
                semestre=1,
                promedio=1.2,
                risk_score=84,
                risk_level="Crítico",
                accion="Intervención inmediata de Permanencia Estudiantil.",
            ),
        ]
    )
    assert payload.startswith(b"%PDF")
    assert b"10001007" in payload
    assert b"10001001" not in payload


def test_pdf_escapa_marcadores():
    assert "&lt;" in pdf_safe("Ana < Nia")
