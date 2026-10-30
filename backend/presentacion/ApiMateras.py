"""API REST: usuarios, materas y lecturas ESP32."""

import math
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

from aplicacion.GestionMateras import (
    GestionMateras, MateraNoEncontrada, DispositivoOcupado
)
from dominio.modelos.Matera import (
    AccesoNoAutorizado, VinculacionInvalida, LecturaDispositivo
)
from dominio.modelos.Entidades import Medicion
from dominio.modelos.Errores import (
    ParametroInvalidoError, EspecieDesconocidaError
)
from presentacion.Controlador import serializar_diagnostico


def crear_api_materas(usuarios, materas, lecturas, diagnosticar, secreto):
    bp = Blueprint("api_materas", __name__)
    gestion = GestionMateras(materas)

    def fallo(mensaje, estado=400):
        return jsonify({"mensaje": str(mensaje)}), estado

    def cuerpo():
        datos = request.get_json(silent=True)
        return datos if isinstance(datos, dict) else {}

    def token(sujeto, alcance, dias=1):
        ahora = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": sujeto,
                "scope": alcance,
                "iss": "greenmind",
                "iat": ahora,
                "exp": ahora + timedelta(days=dias)
            },
            secreto,
            algorithm="HS256"
        )

    def requiere(alcance):
        def decorador(funcion):
            @wraps(funcion)
            def protegida(*args, **kwargs):
                encabezado = request.headers.get("Authorization", "")

                if not encabezado.startswith("Bearer "):
                    return fallo("Token obligatorio.", 401)

                try:
                    identidad = jwt.decode(
                        encabezado[7:],
                        secreto,
                        algorithms=["HS256"],
                        issuer="greenmind",
                        options={"require": ["sub", "scope", "exp", "iat"]}
                    )
                except jwt.InvalidTokenError:
                    return fallo("Token inválido o vencido.", 401)

                if identidad["scope"] != alcance:
                    return fallo("Permisos insuficientes.", 403)

                sujeto = identidad["sub"]
                if not isinstance(sujeto, str) or not sujeto:
                    return fallo("Identidad inválida.", 401)

                return funcion(sujeto, *args, **kwargs)
            return protegida
        return decorador

    def serializar(matera):
        return {
            "id": matera.id,
            "nombre": matera.nombre,
            "especie": matera.especie,
            "dispositivo": matera.dispositivo_id,
            "activa": matera.activa
        }

    def error_gestion(exc):
        if isinstance(exc, AccesoNoAutorizado):
            return fallo(exc, 403)
        if isinstance(exc, MateraNoEncontrada):
            return fallo(exc, 404)
        if isinstance(exc, (DispositivoOcupado, sqlite3.IntegrityError)):
            return fallo(exc, 409)
        return fallo(exc, 400)

    @bp.post("/api/auth/register")
    def registro():
        datos = cuerpo()
        nombre = str(datos.get("nombre") or "").strip()
        correo = str(datos.get("correo") or "").strip().lower()
        clave = datos.get("contrasena")

        if (not nombre or "@" not in correo or
                not isinstance(clave, str) or len(clave) < 8):
            return fallo("Nombre, correo y contraseña válida requeridos.")

        if usuarios.obtener_por_correo(correo):
            return fallo("Correo ya registrado.", 409)

        try:
            usuarios.crear(
                str(uuid4()), nombre, correo,
                generate_password_hash(clave)
            )
        except sqlite3.IntegrityError:
            return fallo("Correo ya registrado.", 409)

        return jsonify({"mensaje": "Cuenta creada."}), 201

    @bp.post("/api/auth/login")
    def login():
        datos = cuerpo()
        correo = str(datos.get("correo") or "").strip().lower()
        clave = datos.get("contrasena")
        usuario = usuarios.obtener_por_correo(correo) if correo else None

        if (not usuario or not isinstance(clave, str) or
                not check_password_hash(usuario["password_hash"], clave)):
            return fallo("Credenciales incorrectas.", 401)

        return jsonify({
            "token": token(usuario["id"], "user"),
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "correo": usuario["correo"]
            }
        })

    @bp.get("/api/v1/plantas")
    @requiere("user")
    def listar(usuario_id):
        return jsonify({
            "plantas": [
                serializar(m) for m in gestion.listar(usuario_id)
            ]
        })

    @bp.post("/api/v1/plantas")
    @requiere("user")
    def registrar(usuario_id):
        datos = cuerpo()
        dispositivo = str(datos.get("dispositivo") or "").strip()

        # Identificador virtual para desarrollo si no hay QR físico.
        if not dispositivo:
            dispositivo = str(uuid4())

        try:
            matera = gestion.registrar(
                usuario_id,
                dispositivo,
                datos.get("nombre"),
                datos.get("especie")
            )
        except (VinculacionInvalida, DispositivoOcupado,
                sqlite3.IntegrityError) as exc:
            return error_gestion(exc)

        return jsonify({
            "planta": serializar(matera),
            "token_dispositivo": token(
                dispositivo, "readings:write", 30
            )
        }), 201

    @bp.patch("/api/v1/plantas/<planta_id>")
    @requiere("user")
    def editar(usuario_id, planta_id):
        datos = cuerpo()
        try:
            matera = gestion.obtener(usuario_id, planta_id)
            actualizada = gestion.editar(
                usuario_id, planta_id,
                datos.get("nombre", matera.nombre),
                datos.get("especie", matera.especie)
            )
            return jsonify({"planta": serializar(actualizada)})
        except (MateraNoEncontrada, AccesoNoAutorizado,
                VinculacionInvalida, ValueError) as exc:
            return error_gestion(exc)

    @bp.delete("/api/v1/plantas/<planta_id>")
    @requiere("user")
    def desvincular(usuario_id, planta_id):
        try:
            gestion.desvincular(usuario_id, planta_id)
        except (MateraNoEncontrada, AccesoNoAutorizado,
                VinculacionInvalida, ValueError) as exc:
            return error_gestion(exc)

        return jsonify({
            "mensaje": "Matera desvinculada. Historial conservado."
        })

    @bp.get("/api/v1/plantas/<planta_id>/historial")
    @requiere("user")
    def historial(usuario_id, planta_id):
        try:
            gestion.obtener(usuario_id, planta_id)
        except (MateraNoEncontrada, AccesoNoAutorizado) as exc:
            return error_gestion(exc)

        return jsonify({"lecturas": lecturas.historial(planta_id)})

    @bp.get("/api/v1/plantas/<planta_id>/estado")
    @requiere("user")
    def estado(usuario_id, planta_id):
        try:
            matera = gestion.obtener(usuario_id, planta_id)
        except (MateraNoEncontrada, AccesoNoAutorizado) as exc:
            return error_gestion(exc)

        lectura = lecturas.ultima(planta_id)
        diagnostico = None

        if lectura:
            try:
                m = Medicion(
                    lectura["humedad"],
                    lectura["luz"],
                    lectura["temperatura"]
                )
                resultado = diagnosticar.ejecutar(matera.especie, m)
                diagnostico = serializar_diagnostico(resultado)
            except (ParametroInvalidoError, EspecieDesconocidaError):
                pass

        return jsonify({
            "planta": serializar(matera),
            "lectura": lectura,
            "diagnostico": diagnostico
        })

    @bp.post("/api/dispositivos/<dispositivo_id>/lecturas")
    @requiere("readings:write")
    def recibir_lectura(sujeto, dispositivo_id):
        if sujeto != dispositivo_id:
            return fallo("Token de otro dispositivo.", 403)

        matera = materas.obtener_por_dispositivo(dispositivo_id)
        if matera is None:
            return fallo("Dispositivo no vinculado.", 404)

        datos = cuerpo()

        if (datos.get("dispositivo") is not None and
                datos["dispositivo"] != dispositivo_id):
            return fallo("Identificador de lectura incorrecto.", 400)

        try:
            valores = {}
            for campo in ("humedad", "luz", "temperatura"):
                valor = datos.get(campo)
                if (isinstance(valor, bool) or
                        not isinstance(valor, (int, float))):
                    raise ValueError(f"{campo} debe ser numérico.")
                valor = float(valor)
                if not math.isfinite(valor):
                    raise ValueError(f"{campo} debe ser finito.")
                valores[campo] = valor

            medicion = Medicion(**valores)

            fecha_texto = datos.get("fecha")
            if not isinstance(fecha_texto, str):
                raise ValueError("Fecha ISO 8601 obligatoria.")

            fecha = datetime.fromisoformat(
                fecha_texto.replace("Z", "+00:00")
            )
            if fecha.tzinfo is None:
                raise ValueError("La fecha requiere zona horaria.")

            lectura = LecturaDispositivo(
                dispositivo_id=dispositivo_id,
                fecha=fecha,
                humedad=medicion.humedad,
                luz=medicion.luz,
                temperatura=medicion.temperatura
            )
            lecturas.guardar(matera.id, lectura)

        except (ValueError, ParametroInvalidoError,
                VinculacionInvalida) as exc:
            return fallo(exc, 400)

        return jsonify({
            "mensaje": "Lectura registrada.",
            "matera_id": matera.id
        }), 201

    return bp
