import csv
from pathlib import Path

from dominio.modelos.Entidades import Especie, RangoReferencia
from dominio.modelos.I_ProveedorDeRangos import I_ProveedorDeRangos


class ProveedorCsvDeRangos(I_ProveedorDeRangos):

    def __init__(self, ruta_archivo):
        self.ruta_archivo = Path(ruta_archivo)
        self._especies_por_nombre = self._cargar_especies()

    def _cargar_especies(self):
        especies = {}
        with self.ruta_archivo.open(newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                nombre = fila["especie"].strip()
                especies[nombre] = Especie(
                    nombre=nombre,
                    rango_humedad=RangoReferencia(
                        float(fila["humedad_min"]),
                        float(fila["humedad_max"]),
                    ),
                    rango_luz=RangoReferencia(
                        float(fila["luz_min"]),
                        float(fila["luz_max"]),
                    ),
                    rango_temperatura=RangoReferencia(
                        float(fila["temp_min"]),
                        float(fila["temp_max"]),
                    ),
                )
        return especies

    def obtener_especie_por_nombre(self, nombre_especie):
        return self._especies_por_nombre.get(nombre_especie)

    def obtener_todas_las_especies(self):
        return list(self._especies_por_nombre.values())