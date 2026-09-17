from dominio.modelos.Entidades import Medicion
from dominio.modelos.Errores import EspecieDesconocidaError
from dominio.modelos.I_ProveedorDeRangos import I_ProveedorDeRangos
from dominio.modelos.EvaluadorPlanta import EvaluadorDePlanta


class DiagnosticarPlantaCasoDeUso:

    def __init__(self, proveedor_de_rangos, evaluador_de_planta):
        self.proveedor_de_rangos = proveedor_de_rangos
        self.evaluador_de_planta = evaluador_de_planta

    def ejecutar(self, nombre_especie, medicion):
        especie = self.proveedor_de_rangos.obtener_especie_por_nombre(nombre_especie)
        if especie is None:
            raise EspecieDesconocidaError(nombre_especie)
        return self.evaluador_de_planta.diagnosticar(medicion, especie)


class ListarEspeciesCasoDeUso:

    def __init__(self, proveedor_de_rangos):
        self.proveedor_de_rangos = proveedor_de_rangos

    def ejecutar(self):
        return self.proveedor_de_rangos.obtener_todas_las_especies()