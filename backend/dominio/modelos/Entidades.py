from dataclasses import dataclass, field
from enum import Enum

from dominio.modelos.Errores import ParametroInvalidoError


class EstadoParametro(Enum):
    BAJO = "BAJO"
    OPTIMO = "OPTIMO"
    ALTO = "ALTO"


class EstadoGlobal(Enum):
    SALUDABLE = "SALUDABLE"
    EN_RIESGO = "EN RIESGO"
    CRITICO = "CRITICO"


@dataclass(frozen=True)
class RangoReferencia:
    minimo: float
    maximo: float


@dataclass(frozen=True)
class Medicion:
    humedad: float
    luz: float
    temperatura: float

    def __post_init__(self):
        if not (0 <= self.humedad <= 100):
            raise ParametroInvalidoError("humedad", "La humedad debe ser un porcentaje entre 0 y 100.")
        if self.luz < 0:
            raise ParametroInvalidoError("luz", "La luz no puede ser negativa.")
        if not (-20 <= self.temperatura <= 80):
            raise ParametroInvalidoError(
                "temperatura",
                "La temperatura debe estar entre -20 y 80 grados Celsius.",
            )        
        


@dataclass(frozen=True)
class Especie:
    nombre: str
    rango_humedad: RangoReferencia
    rango_luz: RangoReferencia
    rango_temperatura: RangoReferencia


@dataclass(frozen=True)
class ParametroEvaluado:
    nombre: str
    valor: float
    unidad: str
    rango_optimo: RangoReferencia
    estado: EstadoParametro


@dataclass(frozen=True)
class DiagnosticoPlanta:
    nombre_especie: str
    estado_global: EstadoGlobal
    parametros_evaluados: list[ParametroEvaluado] = field(default_factory=list)
    recomendaciones: list[str] = field(default_factory=list)