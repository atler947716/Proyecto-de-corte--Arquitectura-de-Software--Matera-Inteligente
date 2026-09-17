class EspecieDesconocidaError(Exception):
    def __init__(self, nombre_especie):
        super().__init__(f"La especie '{nombre_especie}' no está soportada.")
        self.nombre_especie = nombre_especie


class ParametroInvalidoError(Exception):
    def __init__(self, campo, mensaje):
        super().__init__(mensaje)
        self.campo = campo