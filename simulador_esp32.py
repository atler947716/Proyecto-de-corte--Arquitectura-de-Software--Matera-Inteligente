
"""Simulador ESP32 para GreenMind.

Simula uno o varios dispositivos con lecturas independientes.
Envía datos mediante HTTP y conserva la autenticación JWT.

Ejemplos:

Un dispositivo:
    python simulador_esp32.py --dispositivo 123123

Varios dispositivos:
    python simulador_esp32.py --dispositivos 123123 ESP32-TEST-001

Tokens:
    Un dispositivo: variable DEVICE_TOKEN o --token
    Varios dispositivos: archivo local tokens_dispositivos.json
"""

import argparse
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from pathlib import Path


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
    """Envía una lectura a Flask usando el JWT del dispositivo."""

    dispositivo_url = urllib.parse.quote(dispositivo, safe="")

    url = (
        f"{api.rstrip('/')}/api/dispositivos/"
        f"{dispositivo_url}/lecturas"
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
        with urllib.request.urlopen(
            solicitud,
            timeout=10
        ) as respuesta:

            return (
                respuesta.status,
                respuesta.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        return (
            error.code,
            error.read().decode("utf-8")
        )

    except urllib.error.URLError as error:
        return None, f"Sin conexión: {error.reason}"


def cargar_tokens(ruta):
    """Carga las credenciales individuales desde un JSON local."""

    archivo = Path(ruta)

    if not archivo.exists():
        return {}

    with archivo.open(encoding="utf-8") as f:
        tokens = json.load(f)

    if not isinstance(tokens, dict):
        raise ValueError(
            "El archivo de tokens debe contener un objeto JSON."
        )

    return tokens


def main():

    parser = argparse.ArgumentParser(
        description="Simulador ESP32 multidispositivo de GreenMind"
    )

    parser.add_argument(
        "--api",
        default=os.getenv(
            "GREENMIND_API",
            "http://127.0.0.1:5000"
        )
    )

    grupo = parser.add_mutually_exclusive_group(required=True)

    grupo.add_argument(
        "--dispositivo",
        help="Identificador de una matera"
    )

    grupo.add_argument(
        "--dispositivos",
        nargs="+",
        help="Identificadores de varias materas"
    )

    parser.add_argument(
        "--token",
        default=os.getenv("DEVICE_TOKEN"),
        help="JWT para un solo dispositivo"
    )

    parser.add_argument(
        "--tokens",
        default="tokens_dispositivos.json",
        help="Archivo JSON con JWT por dispositivo"
    )

    parser.add_argument(
        "--intervalo",
        type=float,
        default=5
    )

    parser.add_argument(
        "--cantidad",
        type=int,
        default=0,
        help="Ciclos de simulación; 0 = continuo"
    )

    args = parser.parse_args()

    if args.intervalo <= 0:
        parser.error("--intervalo debe ser mayor que cero")

    if args.cantidad < 0:
        parser.error("--cantidad no puede ser negativa")

    dispositivos = (
        [args.dispositivo]
        if args.dispositivo
        else list(dict.fromkeys(args.dispositivos))
    )

    try:
        tokens = cargar_tokens(args.tokens)
    except (OSError, ValueError) as error:
        parser.error(f"No se pudieron cargar los tokens: {error}")

    # Permite el JWT pasado directamente solo para un dispositivo.
    if args.token:
        if len(dispositivos) != 1:
            parser.error(
                "--token solo es válido con un dispositivo."
            )

        tokens[dispositivos[0]] = args.token

    faltantes = [
        dispositivo
        for dispositivo in dispositivos
        if not isinstance(tokens.get(dispositivo), str)
        or not tokens[dispositivo].strip()
    ]

    if faltantes:
        parser.error(
            "Falta JWT para: "
            + ", ".join(faltantes)
            + ". Configura el archivo indicado en --tokens."
        )

    # Cada dispositivo mantiene su propio contador.
    contadores = {
        dispositivo: 0
        for dispositivo in dispositivos
    }

    print("\nGREENMIND - SIMULADOR ESP32")
    print("API:", args.api)
    print("Dispositivos:", ", ".join(dispositivos))
    print("Intervalo:", args.intervalo, "segundos")
    print("Ciclos:", "Continuos" if args.cantidad == 0 else args.cantidad)
    print("Ctrl+C para detener\n", flush=True)

    ciclo = 0

    try:
        while args.cantidad == 0 or ciclo < args.cantidad:

            ciclo += 1

            for dispositivo in dispositivos:

                contadores[dispositivo] += 1
                numero = contadores[dispositivo]

                lectura, tipo = generar_lectura(
                    dispositivo,
                    numero
                )

                codigo, respuesta = enviar(
                    args.api,
                    dispositivo,
                    tokens[dispositivo],
                    lectura
                )

                print(
                    f"[{numero}] "
                    f"{dispositivo} | "
                    f"{tipo} | HTTP {codigo} | "
                    f"{respuesta}",
                    flush=True
                )

                if codigo == 401:
                    print(
                        f"AVISO: el JWT de {dispositivo} "
                        "es inválido o expiró.",
                        flush=True
                    )

            if args.cantidad == 0 or ciclo < args.cantidad:
                time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\nSimulador detenido.")


if __name__ == "__main__":
    main()
