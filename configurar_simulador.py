
import getpass
import json
import urllib.request
import urllib.error
from pathlib import Path

API = "http://127.0.0.1:5000"

def peticion(ruta, datos=None, token=None):
    cabeceras = {"Content-Type": "application/json"}

    if token:
        cabeceras["Authorization"] = f"Bearer {token}"

    solicitud = urllib.request.Request(
        API + ruta,
        data=json.dumps(datos).encode("utf-8")
        if datos is not None else None,
        headers=cabeceras,
        method="POST" if datos is not None else "GET"
    )

    try:
        with urllib.request.urlopen(solicitud) as respuesta:
            return json.load(respuesta)
    except urllib.error.HTTPError as error:
        mensaje = error.read().decode("utf-8")
        raise SystemExit(f"HTTP {error.code}: {mensaje}")

correo = input("Correo de GreenMind: ").strip()
clave = getpass.getpass("Contraseña: ")
dispositivo = input("ID del dispositivo (ej. 123123): ").strip()

sesion = peticion("/api/auth/login", {
    "correo": correo,
    "contrasena": clave
})

token_usuario = sesion["token"]

plantas = peticion(
    "/api/v1/plantas",
    token=token_usuario
)["plantas"]

planta = next(
    (p for p in plantas if p["dispositivo"] == dispositivo),
    None
)

if planta is None:
    raise SystemExit(
        "Ese dispositivo no pertenece a tu cuenta."
    )

credencial = peticion(
    f"/api/v1/plantas/{planta['id']}/credencial",
    {},
    token_usuario
)

archivo = Path("tokens_dispositivos.json")

tokens = (
    json.loads(archivo.read_text(encoding="utf-8"))
    if archivo.exists() else {}
)

tokens[dispositivo] = credencial["token_dispositivo"]

archivo.write_text(
    json.dumps(tokens, indent=2),
    encoding="utf-8"
)

print(f"\nCredencial configurada para {dispositivo}.")
print("Guardada en tokens_dispositivos.json")
print("No se ha mostrado el JWT.")
