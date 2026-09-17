from pathlib import Path

from flask import Flask
from flask_cors import CORS

from aplicacion.Diagnostico import (
    DiagnosticarPlantaCasoDeUso,
    ListarEspeciesCasoDeUso,
)
from dominio.modelos.EvaluadorPlanta import EvaluadorDePlanta
from infraestructura.Provedorcsv import ProveedorCsvDeRangos
from presentacion.Controlador import crear_blueprint_de_diagnostico


RUTA_ARCHIVO_ESPECIES = (
    Path(__file__).parent / "infraestructura" / "recursos" / "especies.csv"
)


def crear_aplicacion():
    aplicacion = Flask(__name__)
    CORS(aplicacion)

    proveedor_de_rangos = ProveedorCsvDeRangos(RUTA_ARCHIVO_ESPECIES)
    evaluador_de_planta = EvaluadorDePlanta()

    caso_diagnosticar = DiagnosticarPlantaCasoDeUso(
        proveedor_de_rangos, evaluador_de_planta
    )
    caso_listar = ListarEspeciesCasoDeUso(proveedor_de_rangos)

    aplicacion.register_blueprint(
        crear_blueprint_de_diagnostico(caso_diagnosticar, caso_listar)
    )

    return aplicacion


if __name__ == "__main__":
    crear_aplicacion().run(host="0.0.0.0", port=5000, debug=True)