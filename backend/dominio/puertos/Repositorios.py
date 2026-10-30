"""Contratos de persistencia independientes de infraestructura."""

from abc import ABC, abstractmethod


class PuertoRepositorioMateras(ABC):

    @abstractmethod
    def guardar(self, matera):
        pass

    @abstractmethod
    def obtener_por_id(self, matera_id):
        pass

    @abstractmethod
    def obtener_por_dispositivo(self, dispositivo_id):
        """Devuelve únicamente la vinculación activa, si existe."""
        pass

    @abstractmethod
    def listar_por_propietario(self, propietario_id):
        """Devuelve únicamente materas activas del propietario."""
        pass

    @abstractmethod
    def actualizar(self, matera):
        pass


class PuertoRepositorioLecturas(ABC):

    @abstractmethod
    def guardar(self, matera_id, lectura):
        pass

    @abstractmethod
    def ultima(self, matera_id):
        pass

    @abstractmethod
    def historial(self, matera_id):
        pass
