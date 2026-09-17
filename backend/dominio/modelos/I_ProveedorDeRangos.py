from abc import ABC, abstractmethod


class I_ProveedorDeRangos(ABC):
    @abstractmethod
    def obtener_especie_por_nombre(self, nombre_especie):
        ...

    @abstractmethod
    def obtener_todas_las_especies(self):
        ...