from dominio.modelos.Entidades import (
    DiagnosticoPlanta, Especie, EstadoGlobal, EstadoParametro,
    Medicion, ParametroEvaluado, RangoReferencia,
)


CATALOGO_DE_RECOMENDACIONES = {
    "humedad": {
        EstadoParametro.BAJO: "La humedad del sustrato está por debajo del rango recomendado: riegue moderadamente.",
        EstadoParametro.ALTO: "La humedad del sustrato está por encima del rango recomendado: reduzca el riego.",
    },
    "luz": {
        EstadoParametro.BAJO: "El nivel de luz está por debajo del rango recomendado: acerque la planta a una fuente de luz.",
        EstadoParametro.ALTO: "El nivel de luz está por encima del rango recomendado: aleje la planta de la luz directa.",
    },
    "temperatura": {
        EstadoParametro.BAJO: "La temperatura está por debajo del rango recomendado: mueva la planta a un lugar más cálido.",
        EstadoParametro.ALTO: "La temperatura está por encima del rango recomendado: ventile el ambiente.",
    },
}


class EvaluadorDePlanta:

    def diagnosticar(self, medicion, especie):
        evaluaciones = [
            self._evaluar_parametro("humedad", medicion.humedad, "%", especie.rango_humedad),
            self._evaluar_parametro("luz", medicion.luz, "lux", especie.rango_luz),
            self._evaluar_parametro("temperatura", medicion.temperatura, "C", especie.rango_temperatura),
        ]
        estado_global = self._agregar_estado_global(evaluaciones)
        recomendaciones = self._generar_recomendaciones(evaluaciones)
        return DiagnosticoPlanta(
            nombre_especie=especie.nombre,
            estado_global=estado_global,
            parametros_evaluados=evaluaciones,
            recomendaciones=recomendaciones,
        )

    def _evaluar_parametro(self, nombre, valor, unidad, rango_optimo):
        if valor < rango_optimo.minimo:
            estado = EstadoParametro.BAJO
        elif valor > rango_optimo.maximo:
            estado = EstadoParametro.ALTO
        else:
            estado = EstadoParametro.OPTIMO
        return ParametroEvaluado(nombre, valor, unidad, rango_optimo, estado)

    def _agregar_estado_global(self, evaluaciones):
        cantidad_fuera = sum(1 for e in evaluaciones if e.estado != EstadoParametro.OPTIMO)
        if cantidad_fuera == 0:
            return EstadoGlobal.SALUDABLE
        if cantidad_fuera == 1:
            return EstadoGlobal.EN_RIESGO
        return EstadoGlobal.CRITICO

    def _generar_recomendaciones(self, evaluaciones):
        resultado = []
        for e in evaluaciones:
            if e.estado == EstadoParametro.OPTIMO:
                continue
            resultado.append(CATALOGO_DE_RECOMENDACIONES[e.nombre][e.estado])
        return resultado