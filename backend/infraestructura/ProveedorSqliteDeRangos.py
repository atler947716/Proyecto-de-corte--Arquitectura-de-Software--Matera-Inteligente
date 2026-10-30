import csv
import sqlite3
from pathlib import Path

from dominio.modelos.Entidades import Especie, RangoReferencia
from dominio.modelos.I_ProveedorDeRangos import I_ProveedorDeRangos


class ProveedorSqliteDeRangos(I_ProveedorDeRangos):
    """Proveedor de rangos almacenados en SQLite."""

    def __init__(self, ruta_db, ruta_csv):
        self.ruta_db = Path(ruta_db)
        self.ruta_db.parent.mkdir(parents=True, exist_ok=True)
        self._preparar(ruta_csv)

    def _conectar(self):
        conexion = sqlite3.connect(str(self.ruta_db))
        conexion.row_factory = sqlite3.Row
        return conexion

    def _preparar(self, ruta_csv):
        with self._conectar() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS rangos_especies (
                    nombre TEXT PRIMARY KEY,
                    humedad_min REAL NOT NULL,
                    humedad_max REAL NOT NULL,
                    luz_min REAL NOT NULL,
                    luz_max REAL NOT NULL,
                    temp_min REAL NOT NULL,
                    temp_max REAL NOT NULL
                )
            """)

            cantidad = db.execute(
                "SELECT COUNT(*) FROM rangos_especies"
            ).fetchone()[0]

            if cantidad == 0:
                with Path(ruta_csv).open(
                    encoding="utf-8", newline=""
                ) as archivo:
                    filas = list(csv.DictReader(archivo))

                db.executemany("""
                    INSERT INTO rangos_especies VALUES
                    (?, ?, ?, ?, ?, ?, ?)
                """, [
                    (
                        f["especie"].strip(),
                        float(f["humedad_min"]),
                        float(f["humedad_max"]),
                        float(f["luz_min"]),
                        float(f["luz_max"]),
                        float(f["temp_min"]),
                        float(f["temp_max"])
                    )
                    for f in filas
                ])

    @staticmethod
    def _convertir(fila):
        return Especie(
            nombre=fila["nombre"],
            rango_humedad=RangoReferencia(
                fila["humedad_min"], fila["humedad_max"]
            ),
            rango_luz=RangoReferencia(
                fila["luz_min"], fila["luz_max"]
            ),
            rango_temperatura=RangoReferencia(
                fila["temp_min"], fila["temp_max"]
            )
        )

    def obtener_especie_por_nombre(self, nombre_especie):
        with self._conectar() as db:
            fila = db.execute(
                "SELECT * FROM rangos_especies WHERE nombre = ?",
                (nombre_especie,)
            ).fetchone()

        return self._convertir(fila) if fila else None

    def obtener_todas_las_especies(self):
        with self._conectar() as db:
            filas = db.execute(
                "SELECT * FROM rangos_especies ORDER BY nombre"
            ).fetchall()

        return [self._convertir(f) for f in filas]
