from dataclasses import dataclass

from dominio.modelos.Entidades import Medicion
from dominio.modelos.Errores import ParametroInvalidoError


@dataclass(frozen=True)
class SolicitudDiagnostico:
    nombre_especie: str
    medicion: Medicion


CAMPOS_REQUERIDOS = ("especie", "humedad", "luz", "temperatura")


def construir_solicitud_diagnostico(datos_peticion):
    for campo in CAMPOS_REQUERIDOS:
        if campo not in datos_peticion:
            raise ParametroInvalidoError(campo, f"El campo '{campo}' es obligatorio.")

    nombre_especie = datos_peticion["especie"]
    if not isinstance(nombre_especie, str) or not nombre_especie.strip():
        raise ParametroInvalidoError("especie", "El campo 'especie' debe ser una cadena no vacía.")

    try:
        humedad = float(datos_peticion["humedad"])
        luz = float(datos_peticion["luz"])
        temperatura = float(datos_peticion["temperatura"])
    except (TypeError, ValueError):
        raise ParametroInvalidoError("parametro", "Los parámetros deben ser numéricos.")

    medicion = Medicion(humedad=humedad, luz=luz, temperatura=temperatura)
    return SolicitudDiagnostico(nombre_especie=nombre_especie.strip(), medicion=medicion)