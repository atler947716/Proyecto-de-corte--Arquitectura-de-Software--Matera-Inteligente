"""Casos de uso de gestión de materas.

No dependen de Flask, JWT ni SQLite.
"""

from uuid import uuid4

from dominio.modelos.Matera import (
    Matera,
    AccesoNoAutorizado,
    VinculacionInvalida,
)


class MateraNoEncontrada(Exception):
    pass


class DispositivoOcupado(Exception):
    pass


class GestionMateras:

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def registrar(
        self,
        propietario_id,
        dispositivo_id,
        nombre,
        especie
    ):
        if not propietario_id or not propietario_id.strip():
            raise VinculacionInvalida(
                "El propietario es obligatorio."
            )

        if not dispositivo_id or not dispositivo_id.strip():
            raise VinculacionInvalida(
                "El identificador del dispositivo es obligatorio."
            )

        if not nombre or not nombre.strip():
            raise VinculacionInvalida(
                "El nombre de la planta es obligatorio."
            )

        if not especie or not especie.strip():
            raise VinculacionInvalida(
                "La especie es obligatoria."
            )

        dispositivo_id = dispositivo_id.strip()

        vinculacion = self.repositorio.obtener_por_dispositivo(
            dispositivo_id
        )

        if vinculacion is not None:
            raise DispositivoOcupado(
                "El dispositivo ya tiene una vinculación activa."
            )

        matera = Matera(
            id=str(uuid4()),
            propietario_id=propietario_id,
            dispositivo_id=dispositivo_id,
            nombre=nombre.strip(),
            especie=especie.strip()
        )

        self.repositorio.guardar(matera)

        return matera

    def listar(self, propietario_id):
        return self.repositorio.listar_por_propietario(
            propietario_id
        )

    def obtener(self, propietario_id, matera_id):
        matera = self.repositorio.obtener_por_id(matera_id)

        if matera is None or not matera.activa:
            raise MateraNoEncontrada(
                "La matera solicitada no existe."
            )

        matera.verificar_propietario(propietario_id)

        return matera

    def editar(
        self,
        propietario_id,
        matera_id,
        nombre,
        especie
    ):
        matera = self.obtener(
            propietario_id,
            matera_id
        )

        matera.editar(
            propietario_id,
            nombre,
            especie
        )

        self.repositorio.actualizar(matera)

        return matera

    def desvincular(self, propietario_id, matera_id):
        matera = self.obtener(
            propietario_id,
            matera_id
        )

        matera.desvincular(propietario_id)

        self.repositorio.actualizar(matera)

        return matera
