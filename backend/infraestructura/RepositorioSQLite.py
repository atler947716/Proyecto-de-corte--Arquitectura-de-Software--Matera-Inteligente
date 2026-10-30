"""Adaptadores SQLite para materas, lecturas y usuarios."""

import os
import sqlite3
from pathlib import Path

from dominio.modelos.Matera import Matera
from dominio.puertos.Repositorios import (
    PuertoRepositorioMateras,
    PuertoRepositorioLecturas,
)

RUTA_PREDETERMINADA = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "greenmind.sqlite3"
)


class ConexionSQLite:
    def __init__(self, ruta=None):
        self.ruta = str(
            ruta or os.getenv("GREENMIND_DB", RUTA_PREDETERMINADA)
        )

        Path(self.ruta).parent.mkdir(
            parents=True,
            exist_ok=True
        )
        self.crear_tablas()

    def conectar(self):
        conexion = sqlite3.connect(
            self.ruta,
            timeout=10
        )
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.execute("PRAGMA busy_timeout = 10000")
        return conexion

    def crear_tablas(self):
        with self.conectar() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    fecha_creacion TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS materas (
                    id TEXT PRIMARY KEY,
                    propietario_id TEXT NOT NULL,
                    dispositivo_id TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    especie TEXT NOT NULL,
                    activa INTEGER NOT NULL DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,
                    fecha_desvinculacion TEXT,
                    FOREIGN KEY(propietario_id)
                        REFERENCES usuarios(id)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_dispositivo_activo
                ON materas(dispositivo_id)
                WHERE activa = 1;

                CREATE INDEX IF NOT EXISTS
                    idx_materas_propietario
                ON materas(propietario_id, activa);

                CREATE TABLE IF NOT EXISTS lecturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    matera_id TEXT NOT NULL,
                    dispositivo_id TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    humedad REAL NOT NULL,
                    luz REAL NOT NULL,
                    temperatura REAL NOT NULL,
                    FOREIGN KEY(matera_id)
                        REFERENCES materas(id)
                );

                CREATE INDEX IF NOT EXISTS
                    idx_lecturas_matera_fecha
                ON lecturas(matera_id, fecha DESC);
            """)


class RepositorioUsuariosSQLite:
    def __init__(self, conexion):
        self.conexion = conexion

    def crear(self, usuario_id, nombre, correo, password_hash):
        with self.conexion.conectar() as db:
            db.execute(
                """
                INSERT INTO usuarios
                    (id, nombre, correo, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (
                    usuario_id,
                    nombre,
                    correo.lower().strip(),
                    password_hash
                )
            )

    def obtener_por_correo(self, correo):
        with self.conexion.conectar() as db:
            fila = db.execute(
                "SELECT * FROM usuarios WHERE correo = ?",
                (correo.lower().strip(),)
            ).fetchone()

        return dict(fila) if fila else None

    def obtener_por_id(self, usuario_id):
        with self.conexion.conectar() as db:
            fila = db.execute(
                "SELECT * FROM usuarios WHERE id = ?",
                (usuario_id,)
            ).fetchone()

        return dict(fila) if fila else None


    def actualizar_nombre(self, usuario_id, nombre):
        with self.conexion.conectar() as db:
            resultado = db.execute(
                "UPDATE usuarios SET nombre = ? WHERE id = ?",
                (nombre, usuario_id)
            )
            return resultado.rowcount == 1


    def eliminar_cuenta_y_datos(self, usuario_id):
        """Elimina cuenta y registros asociados atomicamente."""
        with self.conexion.conectar() as db:
            existe = db.execute(
                "SELECT 1 FROM usuarios WHERE id = ?",
                (usuario_id,)
            ).fetchone()

            if existe is None:
                return False

            # Incluye historiales de materas desvinculadas.
            db.execute("""
                DELETE FROM lecturas
                WHERE matera_id IN (
                    SELECT id FROM materas
                    WHERE propietario_id = ?
                )
            """, (usuario_id,))

            db.execute(
                "DELETE FROM materas WHERE propietario_id = ?",
                (usuario_id,)
            )

            db.execute(
                "DELETE FROM usuarios WHERE id = ?",
                (usuario_id,)
            )

            return True


class RepositorioMaterasSQLite(PuertoRepositorioMateras):
    def __init__(self, conexion):
        self.conexion = conexion

    @staticmethod
    def _convertir(fila):
        if fila is None:
            return None

        return Matera(
            id=fila["id"],
            propietario_id=fila["propietario_id"],
            dispositivo_id=fila["dispositivo_id"],
            nombre=fila["nombre"],
            especie=fila["especie"],
            activa=bool(fila["activa"])
        )

    def guardar(self, matera):
        with self.conexion.conectar() as db:
            db.execute(
                """
                INSERT INTO materas
                    (id, propietario_id, dispositivo_id,
                     nombre, especie, activa)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    matera.id,
                    matera.propietario_id,
                    matera.dispositivo_id,
                    matera.nombre,
                    matera.especie,
                    int(matera.activa)
                )
            )

    def obtener_por_id(self, matera_id):
        with self.conexion.conectar() as db:
            fila = db.execute(
                "SELECT * FROM materas WHERE id = ?",
                (matera_id,)
            ).fetchone()

        return self._convertir(fila)

    def obtener_por_dispositivo(self, dispositivo_id):
        with self.conexion.conectar() as db:
            fila = db.execute(
                """
                SELECT * FROM materas
                WHERE dispositivo_id = ?
                  AND activa = 1
                """,
                (dispositivo_id,)
            ).fetchone()

        return self._convertir(fila)

    def listar_por_propietario(self, propietario_id):
        with self.conexion.conectar() as db:
            filas = db.execute(
                """
                SELECT * FROM materas
                WHERE propietario_id = ?
                  AND activa = 1
                ORDER BY fecha_creacion DESC, id DESC
                """,
                (propietario_id,)
            ).fetchall()

        return [self._convertir(fila) for fila in filas]

    def listar_dispositivos_activos(self):
        with self.conexion.conectar() as db:
            filas = db.execute(
                """
                SELECT dispositivo_id FROM materas
                WHERE activa = 1
                """
            ).fetchall()

        return [fila["dispositivo_id"] for fila in filas]

    def actualizar(self, matera):
        with self.conexion.conectar() as db:
            cursor = db.execute(
                """
                UPDATE materas
                SET nombre = ?,
                    especie = ?,
                    activa = ?,
                    fecha_desvinculacion =
                        CASE
                          WHEN ? = 0
                          THEN COALESCE(
                              fecha_desvinculacion,
                              CURRENT_TIMESTAMP
                          )
                          ELSE NULL
                        END
                WHERE id = ?
                  AND propietario_id = ?
                  AND activa = 1
                """,
                (
                    matera.nombre,
                    matera.especie,
                    int(matera.activa),
                    int(matera.activa),
                    matera.id,
                    matera.propietario_id
                )
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "La vinculación no existe o ya está inactiva."
                )


class RepositorioLecturasSQLite(PuertoRepositorioLecturas):
    def __init__(self, conexion):
        self.conexion = conexion

    def guardar(self, matera_id, lectura):
        with self.conexion.conectar() as db:
            cursor = db.execute(
                """
                INSERT INTO lecturas
                    (matera_id, dispositivo_id, fecha,
                     humedad, luz, temperatura)
                SELECT id, dispositivo_id, ?, ?, ?, ?
                FROM materas
                WHERE id = ?
                  AND dispositivo_id = ?
                  AND activa = 1
                """,
                (
                    lectura.fecha.isoformat(),
                    lectura.humedad,
                    lectura.luz,
                    lectura.temperatura,
                    matera_id,
                    lectura.dispositivo_id
                )
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "La matera está inactiva o el dispositivo no coincide."
                )

    def ultima(self, matera_id):
        with self.conexion.conectar() as db:
            fila = db.execute(
                """
                SELECT * FROM lecturas
                WHERE matera_id = ?
                ORDER BY fecha DESC, id DESC
                LIMIT 1
                """,
                (matera_id,)
            ).fetchone()

        return dict(fila) if fila else None

    def historial(self, matera_id, limite=50):
        limite = max(1, min(int(limite), 500))

        with self.conexion.conectar() as db:
            filas = db.execute(
                """
                SELECT * FROM lecturas
                WHERE matera_id = ?
                ORDER BY fecha DESC, id DESC
                LIMIT ?
                """,
                (matera_id, limite)
            ).fetchall()

        return [dict(fila) for fila in filas]
