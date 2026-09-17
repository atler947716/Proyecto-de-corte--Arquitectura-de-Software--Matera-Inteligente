import pytest

from dominio.modelos.Entidades import (
    DiagnosticoPlanta,
    Especie,
    EstadoGlobal,
    EstadoParametro,
    Medicion,
    ParametroEvaluado,
    RangoReferencia,
)
from dominio.modelos.Errores import (
    EspecieDesconocidaError,
    ParametroInvalidoError,
)
from dominio.modelos.EvaluadorPlanta import EvaluadorDePlanta
def test_medicion_valida_se_construye():
    m = Medicion(humedad=30, luz=800, temperatura=22)
    assert m.humedad == 30
    assert m.luz == 800
    assert m.temperatura == 22


def test_medicion_con_humedad_mayor_a_100_falla():
    with pytest.raises(ParametroInvalidoError) as info:
        Medicion(humedad=150, luz=800, temperatura=22)
    assert info.value.campo == "humedad"


def test_medicion_con_humedad_negativa_falla():
    with pytest.raises(ParametroInvalidoError) as info:
        Medicion(humedad=-5, luz=800, temperatura=22)
    assert info.value.campo == "humedad"


def test_medicion_con_luz_negativa_falla():
    with pytest.raises(ParametroInvalidoError) as info:
        Medicion(humedad=30, luz=-100, temperatura=22)
    assert info.value.campo == "luz"


def test_medicion_con_temperatura_mayor_a_80_falla():
    with pytest.raises(ParametroInvalidoError) as info:
        Medicion(humedad=30, luz=800, temperatura=100)
    assert info.value.campo == "temperatura"


def test_medicion_con_temperatura_menor_a_menos_20_falla():
    with pytest.raises(ParametroInvalidoError) as info:
        Medicion(humedad=30, luz=800, temperatura=-40)
    assert info.value.campo == "temperatura"


def test_especie_desconocida_guarda_nombre():
    e = EspecieDesconocidaError("sansevieria")
    assert e.nombre_especie == "sansevieria"


def test_parametro_invalido_guarda_campo():
    e = ParametroInvalidoError("humedad", "mensaje")
    assert e.campo == "humedad"


@pytest.fixture
def especie():
    return Especie(
        nombre="sansevieria",
        rango_humedad=RangoReferencia(20, 45),
        rango_luz=RangoReferencia(200, 1500),
        rango_temperatura=RangoReferencia(15, 29),
    )


def test_todos_los_parametros_en_rango_es_saludable(especie):
    d = EvaluadorDePlanta().diagnosticar(Medicion(30, 800, 22), especie)
    assert d.estado_global == EstadoGlobal.SALUDABLE
    assert d.recomendaciones == []


def test_humedad_baja_genera_en_riesgo(especie):
    d = EvaluadorDePlanta().diagnosticar(Medicion(10, 800, 22), especie)
    humedad = next(p for p in d.parametros_evaluados if p.nombre == "humedad")
    assert humedad.estado == EstadoParametro.BAJO
    assert d.estado_global == EstadoGlobal.EN_RIESGO
    assert len(d.recomendaciones) == 1


def test_luz_alta_genera_en_riesgo(especie):
    d = EvaluadorDePlanta().diagnosticar(Medicion(30, 3000, 22), especie)
    luz = next(p for p in d.parametros_evaluados if p.nombre == "luz")
    assert luz.estado == EstadoParametro.ALTO
    assert d.estado_global == EstadoGlobal.EN_RIESGO


def test_dos_parametros_fuera_de_rango_generan_critico(especie):
    d = EvaluadorDePlanta().diagnosticar(Medicion(10, 3000, 22), especie)
    assert d.estado_global == EstadoGlobal.CRITICO
    assert len(d.recomendaciones) == 2


def test_tres_parametros_fuera_de_rango_generan_critico(especie):
    d = EvaluadorDePlanta().diagnosticar(Medicion(5, 5000, 40), especie)
    assert d.estado_global == EstadoGlobal.CRITICO
    assert len(d.recomendaciones) == 3


def test_valores_en_el_limite_son_optimos(especie):
    d = EvaluadorDePlanta().diagnosticar(Medicion(20, 200, 15), especie)
    assert d.estado_global == EstadoGlobal.SALUDABLE