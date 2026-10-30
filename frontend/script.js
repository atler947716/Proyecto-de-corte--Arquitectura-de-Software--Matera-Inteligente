"use strict";

// GREENMIND — FRONTEND CONECTADO A FLASK
const API = window.location.origin;
const $ = id => document.getElementById(id);

let token = sessionStorage.getItem("greenmind_jwt") || "";
let usuario = null;
let plantas = [];
let seleccionada = null;
let intervalo = null;
let especiesDisponibles = [];

function aviso(texto, error = false) {
    const mensaje = $("mensaje");
    mensaje.textContent = texto;
    mensaje.style.color = error ? "#ff9b95" : "#76d9a5";
}

async function peticion(ruta, metodo = "GET", cuerpo = null) {
    const opciones = {
        method: metodo,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (token) {
        opciones.headers.Authorization = `Bearer ${token}`;
    }

    if (cuerpo !== null) {
        opciones.body = JSON.stringify(cuerpo);
    }

    let respuesta;
    try {
        respuesta = await fetch(API + ruta, opciones);
    } catch {
        throw new Error("No hay conexión con Flask.");
    }

    const datos = await respuesta.json().catch(() => ({}));

    if (!respuesta.ok) {
        if (respuesta.status === 401 && token) {
            cerrarSesion();
        }
        throw new Error(datos.mensaje || `HTTP ${respuesta.status}`);
    }

    return datos;
}

// NAVEGACIÓN
function pantalla(id) {
    ["inicio", "materas", "registrar-planta", "detalle", "perfil"]
        .forEach(nombre => {
            $(nombre).hidden = nombre !== id;
        });

    if (id === "inicio") cargarResumen();
    if (id === "materas") cargarPlantas();
    if (id === "perfil") cargarPerfil();
}

function pantallaAuth(id) {
    ["vista-login", "vista-registro", "vista-recuperar",
     "vista-cambio-clave"].forEach(nombre => {
        $(nombre).hidden = nombre !== id;
    });
}

function mostrarPanel() {
    $("auth").hidden = true;
    $("panel").hidden = false;
    pantalla("inicio");
    iniciarActualizacion();
}

function cerrarSesion() {
    token = "";
    usuario = null;
    seleccionada = null;
    plantas = [];
    sessionStorage.removeItem("greenmind_jwt");

    clearInterval(intervalo);
    intervalo = null;

    $("auth").hidden = false;
    $("panel").hidden = true;
    pantallaAuth("vista-login");
}

// AUTENTICACIÓN
async function iniciarSesion(evento) {
    evento.preventDefault();

    const datos = new FormData(evento.currentTarget);

    try {
        const resultado = await peticion("/api/auth/login", "POST", {
            correo: datos.get("correo"),
            contrasena: datos.get("contrasena")
        });

        if (!resultado.token) {
            throw new Error("El backend no entregó el JWT.");
        }

        token = resultado.token;
        usuario = resultado.usuario;
        sessionStorage.setItem("greenmind_jwt", token);

        if (usuario) {
            $("perfil-correo").value = usuario.correo || "";
            $("perfil-nombre").value = usuario.nombre || "";
        }

        mostrarPanel();
        aviso("Sesión iniciada.");

    } catch (error) {
        aviso(error.message, true);
    }
}

async function registrarUsuario(evento) {
    evento.preventDefault();

    if ($("contrasena-registro").value !==
        $("confirmar-registro").value) {
        aviso("Las contraseñas no coinciden.", true);
        return;
    }

    const formulario = evento.currentTarget;
    const datos = new FormData(formulario);

    try {
        await peticion("/api/auth/register", "POST", {
            nombre: datos.get("nombre"),
            correo: datos.get("correo"),
            contrasena: datos.get("contrasena")
        });

        formulario.reset();
        pantallaAuth("vista-login");
        aviso("Cuenta registrada. Inicia sesión.");

    } catch (error) {
        aviso(error.message, true);
    }
}

// ESPECIES
async function cargarEspecies() {
    const resultado = await peticion("/api/v1/especies");
    especiesDisponibles = resultado;

    for (const id of ["especies", "editar-especie"]) {
        const selector = $(id);
        selector.replaceChildren();

        const inicial = document.createElement("option");
        inicial.value = "";
        inicial.textContent = "Selecciona una especie";
        selector.appendChild(inicial);

        resultado.forEach(especie => {
            const opcion = document.createElement("option");
            opcion.value = especie.nombre;
            opcion.textContent = especie.nombre;
            selector.appendChild(opcion);
        });
    }
}

// MATERAS
async function cargarPlantas() {
    if (!token) return;

    try {
        const resultado = await peticion("/api/v1/plantas");
        plantas = resultado.plantas || [];

        const contenedor = $("plantas");
        contenedor.replaceChildren();

        if (!plantas.length) {
            contenedor.textContent =
                "Todavía no hay materas registradas.";
            return;
        }

        plantas.forEach(planta => {
            const boton = document.createElement("button");
            boton.type = "button";
            boton.className = "planta";
            boton.textContent =
                `${planta.nombre} · ${planta.especie}`;

            boton.addEventListener("click", () => {
                seleccionada = planta.id;
                pantalla("detalle");
                cargarDetalle();
            });

            contenedor.appendChild(boton);
        });

    } catch (error) {
        aviso(error.message, true);
    }
}

async function registrarPlanta(evento) {
    evento.preventDefault();

    const formulario = evento.currentTarget;
    const datos = new FormData(formulario);
    
    const dispositivo = $("identificador-registro").value.trim();

    if (!dispositivo) {
        aviso("Introduce el identificador del dispositivo.", true);
        return;
    }

    try {
        const resultado = await peticion(
            "/api/v1/plantas",
            "POST",
            {
                nombre: datos.get("nombre"),
                especie: datos.get("especie"),
                dispositivo
            }
        );

        formulario.reset();
        $("identificador-registro").value = "";
        $("qr-manual").value = "";

        pantalla("materas");

        // El token del dispositivo es distinto al JWT del usuario.
        // No se guarda en localStorage ni se imprime en consola.
        if (resultado.token_dispositivo) {
            aviso(
                "Matera registrada. El backend emitió una credencial " +
                "de dispositivo; falta configurar el simulador."
            );
        } else {
            aviso("Matera registrada.");
        }

    } catch (error) {
        aviso(error.message, true);
    }
}

// DIAGNÓSTICO
function mostrarMedidas(lectura) {
    const contenedor = $("medidas");
    contenedor.replaceChildren();

    if (!lectura) return;

    [
        ["Humedad", lectura.humedad, "%"],
        ["Luz", lectura.luz, "lux"],
        ["Temperatura", lectura.temperatura, "°C"]
    ].forEach(([nombre, valor, unidad]) => {
        const bloque = document.createElement("div");
        const titulo = document.createElement("strong");
        const texto = document.createElement("p");

        titulo.textContent = nombre;
        texto.textContent = `${valor} ${unidad}`;

        bloque.append(titulo, texto);
        contenedor.appendChild(bloque);
    });
}

async function cargarDetalle() {
    if (!seleccionada || !token) return;

    const id = seleccionada;

    try {
        const [estado, historial] = await Promise.all([
            peticion(`/api/v1/plantas/${encodeURIComponent(id)}/estado`),
            peticion(`/api/v1/plantas/${encodeURIComponent(id)}/historial`)
        ]);

        if (id !== seleccionada) return;

        const planta = estado.planta;
        const lectura = estado.lectura;
        const diagnostico = estado.diagnostico;

        $("titulo").textContent = planta.nombre;
        $("detalle-especie").textContent = planta.especie;
        $("detalle-identificador").textContent =
            `Dispositivo: ${planta.dispositivo}`;

        $("estado").textContent =
            diagnostico?.estado || "No disponible";

        $("estado-datos").textContent = lectura
            ? "Última lectura registrada"
            : "Sin mediciones disponibles";

        $("fecha").textContent = lectura
            ? new Date(lectura.fecha).toLocaleString("es-CO")
            : "";

        mostrarMedidas(lectura);

        const recomendaciones = $("recomendaciones");
        recomendaciones.replaceChildren();

        if (diagnostico?.recomendaciones?.length) {
            diagnostico.recomendaciones.forEach(texto => {
                const p = document.createElement("p");
                p.textContent = texto;
                recomendaciones.appendChild(p);
            });
        } else {
            recomendaciones.textContent =
                lectura
                    ? "Sin recomendaciones adicionales."
                    : "Esperando lecturas válidas.";
        }

        const zonaHistorial = $("historial");
        zonaHistorial.replaceChildren();

        (historial.lecturas || []).forEach(l => {
            const fila = document.createElement("p");
            fila.textContent =
                `${new Date(l.fecha).toLocaleString("es-CO")} · ` +
                `H ${l.humedad}% · L ${l.luz} lux · ` +
                `T ${l.temperatura} °C`;
            zonaHistorial.appendChild(fila);
        });

        if (!(historial.lecturas || []).length) {
            zonaHistorial.textContent = "Sin lecturas registradas.";
        }

    } catch (error) {
        aviso(error.message, true);
    }
}

// EDICIÓN Y DESVINCULACIÓN
function abrirEdicion() {
    const planta = plantas.find(p => p.id === seleccionada);
    if (!planta) return;

    $("editar-nombre").value = planta.nombre;
    $("editar-especie").value = planta.especie;
    $("editar-dispositivo").value = planta.dispositivo;
    $("editar-planta").hidden = false;
}

async function guardarEdicion(evento) {
    evento.preventDefault();

    if (!seleccionada) return;

    try {
        await peticion(
            `/api/v1/plantas/${encodeURIComponent(seleccionada)}`,
            "PATCH",
            {
                nombre: $("editar-nombre").value.trim(),
                especie: $("editar-especie").value
            }
        );

        $("editar-planta").hidden = true;
        await cargarPlantas();
        await cargarDetalle();
        aviso("Planta actualizada.");

    } catch (error) {
        aviso(error.message, true);
    }
}

async function desvincular() {
    if (!seleccionada) return;

    try {
        await peticion(
            `/api/v1/plantas/${encodeURIComponent(seleccionada)}`,
            "DELETE"
        );

        seleccionada = null;
        $("confirmar-desvinculacion").hidden = true;

        pantalla("materas");
        aviso("Matera desvinculada. Historial conservado en SQLite.");

    } catch (error) {
        aviso(error.message, true);
    }
}

// RESUMEN

async function cargarResumen() {
    if (!token) return;

    try {
        // Consultar las materas del usuario autenticado.
        const resultado = await peticion("/api/v1/plantas");
        plantas = resultado.plantas || [];

        const contadores = {
            bien: 0,
            regular: 0,
            mal: 0,
            sinDatos: 0
        };

        const alertas = [];

        // Consultar los diagnósticos reales de todas las materas.
        const resultados = await Promise.allSettled(
            plantas.map(planta =>
                peticion(
                    `/api/v1/plantas/${encodeURIComponent(planta.id)}/estado`
                )
            )
        );

        resultados.forEach((resultado, indice) => {
            const planta = plantas[indice];

            if (resultado.status === "rejected") {
                contadores.sinDatos++;
                return;
            }

            const diagnostico = resultado.value.diagnostico;

            if (!diagnostico) {
                contadores.sinDatos++;
                return;
            }

            switch (diagnostico.estado) {
                case "SALUDABLE":
                    contadores.bien++;
                    break;

                case "EN RIESGO":
                    contadores.regular++;
                    break;

                case "CRITICO":
                    contadores.mal++;
                    break;

                default:
                    contadores.sinDatos++;
            }

            if (diagnostico.estado !== "SALUDABLE") {
                alertas.push(
                    `${planta.nombre}: ${diagnostico.estado}`
                );
            }
        });

        // Actualizar los cuatro indicadores del Inicio.
        $("total-bien").textContent = contadores.bien;
        $("total-regular").textContent = contadores.regular;
        $("total-mal").textContent = contadores.mal;
        $("total-sin-datos").textContent = contadores.sinDatos;

        // Mostrar alertas reales.
        $("alertas-inicio").textContent = alertas.length
            ? alertas.join(" | ")
            : "No hay alertas activas.";

        $("cambios-inicio").textContent =
            `${plantas.length} materas registradas.`;

    } catch (error) {
        aviso("Error al cargar el resumen: " + error.message, true);
    }
}



function iniciarActualizacion() {
    clearInterval(intervalo);

    intervalo = setInterval(() => {
        if (!token) return;

        if (!$("detalle").hidden && seleccionada) {
            cargarDetalle();
        }

        if (!$("inicio").hidden) {
            cargarResumen();
        }
    }, 5000);
}



async function cargarPerfil() {
    if (!token) return;

    try {
        const datos = await peticion("/api/auth/perfil");

        usuario = datos;
        $("perfil-nombre").value = datos.nombre;
        $("perfil-correo").value = datos.correo;

    } catch (error) {
        aviso("Error al cargar perfil: " + error.message, true);
    }
}

async function guardarPerfil(evento) {
    evento.preventDefault();

    const nombre = $("perfil-nombre").value.trim();

    if (nombre.length < 2 || nombre.length > 100) {
        aviso("El nombre debe tener entre 2 y 100 caracteres.", true);
        return;
    }

    try {
        const resultado = await peticion(
            "/api/auth/perfil",
            "PATCH",
            { nombre }
        );

        usuario = resultado.usuario;

        $("perfil-nombre").value = usuario.nombre;
        $("perfil-correo").value = usuario.correo;

        aviso("Perfil actualizado correctamente.");

    } catch (error) {
        aviso("Error al guardar perfil: " + error.message, true);
    }
}

async function eliminarCuenta(evento) {
    evento.preventDefault();

    if (!$("eliminar-confirmacion").checked) {
        aviso("Confirma la eliminacion.", true);
        return;
    }

    const clave = $("eliminar-clave").value;

    const confirmado = window.confirm(
        "Eliminar permanentemente tu cuenta, " +
        "todas tus materas y sus historiales? " +
        "Esta accion NO se puede deshacer."
    );

    if (!confirmado) return;

    const boton = evento.currentTarget.querySelector(
        'button[type="submit"]'
    );

    boton.disabled = true;

    try {
        await peticion(
            "/api/auth/perfil",
            "DELETE",
            { contrasena: clave }
        );

        cerrarSesion();

        $("formulario-eliminar-cuenta").reset();
        $("zona-eliminar-cuenta").hidden = true;

        aviso("Cuenta y datos eliminados permanentemente.");

    } catch (error) {
        aviso("Error al eliminar cuenta: " + error.message, true);
    } finally {
        boton.disabled = false;
    }
}

// EVENTOS
document.addEventListener("DOMContentLoaded", async () => {
    document.querySelectorAll("[data-pantalla]").forEach(b => {
        b.addEventListener("click", () => pantalla(b.dataset.pantalla));
    });

    document.querySelectorAll("[data-auth-vista]").forEach(b => {
        b.addEventListener("click", () => pantallaAuth(b.dataset.authVista));
    });

    document.querySelectorAll(".alternar-clave").forEach(c => {
        c.addEventListener("change", () => {
            c.dataset.objetivo.split(",").forEach(id => {
                const campo = $(id);
                if (campo) {
                    campo.type = c.checked ? "text" : "password";
                }
            });
        });
    });

    $("login").addEventListener("submit", iniciarSesion);
    $("registro").addEventListener("submit", registrarUsuario);

    $("editar-perfil").addEventListener(
        "submit", guardarPerfil
    );

    $("abrir-eliminar-cuenta").addEventListener("click", () => {
        $("zona-eliminar-cuenta").hidden = false;
    });

    $("cancelar-eliminar-cuenta").addEventListener("click", () => {
        $("zona-eliminar-cuenta").hidden = true;
        $("formulario-eliminar-cuenta").reset();
    });

    $("formulario-eliminar-cuenta").addEventListener(
        "submit", eliminarCuenta
    );

    $("salir").addEventListener("click", cerrarSesion);
    $("crear").addEventListener("submit", registrarPlanta);

    $("validar-qr").addEventListener("click", () => {
        const id = $("qr-manual").value.trim();
        if (!id) {
            aviso("Introduce el identificador del QR.", true);
            return;
        }

        // Esto captura el ID, pero no valida el dispositivo en servidor.
        $("identificador-registro").value = id;
        $("estado-qr").textContent =
            "Identificador leído. Disponibilidad pendiente " +
            "de confirmar al registrar.";
    });

    $("activar-camara").addEventListener("click", () =>
        aviso("Escaneo con cámara pendiente de implementación.", true)
    );

    $("reintentar-qr").addEventListener("click", () => {
        $("qr-manual").value = "";
        $("identificador-registro").value = "";
        $("estado-qr").textContent = "Esperando identificador.";
    });

    $("abrir-edicion").addEventListener("click", abrirEdicion);
    $("editar-planta").addEventListener("submit", guardarEdicion);
    $("cancelar-edicion").addEventListener("click", () => {
        $("editar-planta").hidden = true;
    });

    $("abrir-desvinculacion").addEventListener("click", () => {
        $("confirmar-desvinculacion").hidden = false;
    });

    $("cancelar-eliminacion").addEventListener("click", () => {
        $("confirmar-desvinculacion").hidden = true;
    });

    $("confirmar-eliminacion").addEventListener("click", desvincular);

    for (const id of [
        "recuperar-contrasena", "cambiar-contrasena",
        "editar-perfil"
    ]) {
        $(id).addEventListener("submit", evento => {
            evento.preventDefault();
            aviso(
                "Esta función todavía no tiene endpoint en Flask.",
                true
            );
        });
    }

    for (const id of [
        "verificar-cuenta", "reenviar-codigo",
        "solicitar-nuevo-codigo"
    ]) {
        $(id).addEventListener("click", () => {
            aviso("Verificación por correo pendiente de backend.", true);
        });
    }

    $("perfil-cambiar-clave").addEventListener("click", () => {
        $("panel").hidden = true;
        $("auth").hidden = false;
        pantallaAuth("vista-cambio-clave");
    });

    try {
        await cargarEspecies();
    } catch (error) {
        aviso(error.message, true);
    }

    if (token) {
        mostrarPanel();
    }
});
