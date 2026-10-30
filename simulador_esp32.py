"""ESP32 simulado: envía lecturas a GreenMind mediante HTTP.

No requiere hardware ni bibliotecas externas.
El token se obtiene de una variable de entorno o del argumento --token.
"""

import argparse
import json
import os
import random
import time
import urllib.error
import urllib.request

from datetime import datetime, timezone


def generar_lectura(dispositivo, numero):
    """Genera una lectura normal, fuera de rango o inválida."""
    lectura = {
        "dispositivo": dispositivo,
        "fecha": datetime.now(timezone.utc).isoformat(),
        "humedad": round(random.uniform(45, 65), 1),
        "luz": round(random.uniform(500, 1100), 1),
        "temperatura": round(random.uniform(15, 23), 1),
    }

    if numero % 11 == 0:
        lectura["humedad"] = "dato_invalido"
        tipo = "INVALIDA"
    elif numero % 7 == 0:
        lectura["humedad"] = 5
        tipo = "FUERA_DE_RANGO"
    else:
        tipo = "NORMAL"

    return lectura, tipo


def enviar(api, dispositivo, token, lectura):
    url = (
        f"{api.rstrip('/')}/api/dispositivos/"
        f"{dispositivo}/lecturas"
    )

    solicitud = urllib.request.Request(
        url,
        data=json.dumps(lectura).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(solicitud, timeout=10) as respuesta:
            return respuesta.status, respuesta.read().decode("utf-8")

    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")

    except urllib.error.URLError as error:
        return None, f"Sin conexión: {error.reason}"


def main():
    parser = argparse.ArgumentParser(
        description="Simulador HTTP de matera inteligente"
    )
    parser.add_argument(
        "--api",
        default=os.getenv("GREENMIND_API", "http://127.0.0.1:5000"),
    )
    parser.add_argument("--dispositivo", required=True)
    parser.add_argument("--token", default=os.getenv("DEVICE_TOKEN"))
    parser.add_argument("--intervalo", type=float, default=5)
    parser.add_argument(
        "--cantidad",
        type=int,
        default=0,
        help="0 = ejecución continua",
    )

    args = parser.parse_args()

    if not args.token:
        parser.error("Configura DEVICE_TOKEN o utiliza --token")

    if args.intervalo <= 0:
        parser.error("--intervalo debe ser mayor que cero")

    if args.cantidad < 0:
        parser.error("--cantidad no puede ser negativa")

    contador = 0

    print(f"ESP32 simulado: {args.dispositivo}")
    print(f"API: {args.api}")
    print(f"Intervalo: {args.intervalo} segundos")

    try:
        while args.cantidad == 0 or contador < args.cantidad:
            contador += 1

            lectura, tipo = generar_lectura(
                args.dispositivo,
                contador,
            )

            codigo, respuesta = enviar(
                args.api,
                args.dispositivo,
                args.token,
                lectura,
            )

            print(
                f"[{contador}] {tipo} | "
                f"HTTP {codigo} | {respuesta}",
                flush=True,
            )

            if args.cantidad == 0 or contador < args.cantidad:
                time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\nSimulador detenido.")


if __name__ == "__main__":
    main()
