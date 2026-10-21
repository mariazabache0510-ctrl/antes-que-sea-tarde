from app.risk import calcular_riesgo, nivel_y_accion


def test_promedio_alto_sin_otras_senales_es_bajo():
    score, nivel, accion = calcular_riesgo(4.3, 0, 0, 0, 4)
    assert score == 0
    assert nivel == "Bajo"
    assert "ordinario" in accion


def test_caso_medio_de_primer_semestre():
    score, nivel, _accion = calcular_riesgo(3.2, 1, 2, 0, 1)
    assert score == 25
    assert nivel == "Medio"


def test_caso_critico_llega_a_intervencion():
    score, nivel, accion = calcular_riesgo(1.2, 4, 8, 3, 1)
    assert score == 84
    assert nivel == "Crítico"
    assert "inmediata" in accion


def test_el_tope_evita_que_un_indicador_crezca_sin_limite():
    base = calcular_riesgo(4.0, 4, 0, 0, 5)[0]
    exagerado = calcular_riesgo(4.0, 10, 0, 0, 5)[0]
    assert base == exagerado


def test_limites_de_nivel():
    assert nivel_y_accion(24)[0] == "Bajo"
    assert nivel_y_accion(25)[0] == "Medio"
    assert nivel_y_accion(49)[0] == "Medio"
    assert nivel_y_accion(50)[0] == "Alto"
    assert nivel_y_accion(74)[0] == "Alto"
    assert nivel_y_accion(75)[0] == "Crítico"
    assert nivel_y_accion(100)[0] == "Crítico"
