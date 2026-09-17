from flask import Blueprint, jsonify, request

from aplicacion.Diagnostico import (
    DiagnosticarPlantaCasoDeUso,
    ListarEspeciesCasoDeUso,
)
from dominio.modelos.Entidades import DiagnosticoPlanta, Especie
from dominio.modelos.Errores import (
    EspecieDesconocidaError,
    ParametroInvalidoError,
)
from presentacion.dto import construir_solicitud_diagnostico


def serializar_diagnostico(d):
    return {
        "especie": d.nombre_especie,
        "estado": d.estado_global.value,
        "parametros": [
            {
                "nombre": p.nombre,
                "valor": p.valor,
                "unidad": p.unidad,
                "rangoOptimo": [p.rango_optimo.minimo, p.rango_optimo.maximo],
                "estado": p.estado.value,
            }
            for p in d.parametros_evaluados
        ],
        "recomendaciones": list(d.recomendaciones),
    }


def serializar_especie(e):
    return {
        "nombre": e.nombre,
        "rangos": {
            "humedad": [e.rango_humedad.minimo, e.rango_humedad.maximo],
            "luz": [e.rango_luz.minimo, e.rango_luz.maximo],
            "temperatura": [e.rango_temperatura.minimo, e.rango_temperatura.maximo],
        },
    }


def crear_blueprint_de_diagnostico(caso_diagnosticar, caso_listar_especies):
    bp = Blueprint("diagnostico", __name__)

    @bp.route("/api/v1/diagnostics", methods=["POST"])
    def diagnosticar():
        datos = request.get_json(silent=True) or {}

        try:
            solicitud = construir_solicitud_diagnostico(datos)
        except ParametroInvalidoError as error:
            return jsonify({
                "error": "PARAMETRO_INVALIDO",
                "mensaje": str(error),
                "detalle": {"campo": error.campo},
            }), 400

        try:
            diagnostico = caso_diagnosticar.ejecutar(
                solicitud.nombre_especie,
                solicitud.medicion,
            )
        except EspecieDesconocidaError as error:
            return jsonify({
                "error": "ESPECIE NO SOPORTADA",
                "mensaje": str(error),
                "detalle": {"especie": error.nombre_especie},
            }), 404

        return jsonify(serializar_diagnostico(diagnostico)), 200

    @bp.route("/api/v1/especies", methods=["GET"])
    def listar_especies():
        especies = caso_listar_especies.ejecutar()
        return jsonify([serializar_especie(e) for e in especies]), 200

    return bp