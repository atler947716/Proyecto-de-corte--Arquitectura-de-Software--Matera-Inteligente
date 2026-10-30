"""Entidades y reglas de negocio de las materas.

Este módulo no depende de Flask, SQLite, JWT ni HTTP.
"""
from dataclasses import dataclass
from datetime import datetime


class ReglaDeNegocioError(Exception):
    pass


class AccesoNoAutorizado(ReglaDeNegocioError):
    pass


class VinculacionInvalida(ReglaDeNegocioError):
    pass


@dataclass
class Matera:
    id: str
    propietario_id: str
    dispositivo_id: str
    nombre: str
    especie: str
    activa: bool = True

    def verificar_propietario(self, usuario_id: str) -> None:
        if self.propietario_id != usuario_id:
            raise AccesoNoAutorizado(
                "El usuario no es propietario de esta matera."
            )

    def editar(
        self,
        usuario_id: str,
        nombre: str,
        especie: str
    ) -> None:
        self.verificar_propietario(usuario_id)

        if not self.activa:
            raise VinculacionInvalida(
                "No se puede editar una vinculación inactiva."
            )

        if not nombre.strip() or not especie.strip():
            raise VinculacionInvalida(
                "Nombre y especie son obligatorios."
            )

        self.nombre = nombre.strip()
        self.especie = especie.strip()

    def desvincular(self, usuario_id: str) -> None:
        self.verificar_propietario(usuario_id)

        if not self.activa:
            raise VinculacionInvalida(
                "La matera ya está desvinculada."
            )

        self.activa = False


@dataclass(frozen=True)
class LecturaDispositivo:
    dispositivo_id: str
    fecha: datetime
    humedad: float
    luz: float
    temperatura: float

    def __post_init__(self):
        if not self.dispositivo_id.strip():
            raise VinculacionInvalida(
                "El identificador del dispositivo es obligatorio."
            )

        if not isinstance(self.fecha, datetime):
            raise VinculacionInvalida(
                "La fecha de lectura debe ser válida."
            )
