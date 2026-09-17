const URL_BASE_API = "https://shiny-halibut-7v7jrx9wjg95fr7w6-5000.app.github.dev/api/v1";

const formulario = document.getElementById("formulario-diagnostico");
const selectorEspecie = document.getElementById("selector-especie");
const zonaResultado = document.getElementById("zona-resultado");
const zonaError = document.getElementById("zona-error");
const estadoGlobal = document.getElementById("estado-global");
const listaParametros = document.getElementById("lista-parametros");
const listaRecomendaciones = document.getElementById("lista-recomendaciones");
const mensajeError = document.getElementById("mensaje-error");

async function cargarEspecies() {
    try {
        const respuesta = await fetch(`${URL_BASE_API}/especies`);
        const especies = await respuesta.json();

        selectorEspecie.innerHTML = '<option value="">Seleccione una especie</option>';
        for (const especie of especies) {
            const opcion = document.createElement("option");
            opcion.value = especie.nombre;
            opcion.textContent = especie.nombre;
            selectorEspecie.appendChild(opcion);
        }
    } catch (error) {
        selectorEspecie.innerHTML = '<option value="">Error al cargar especies</option>';
    }
}

function mostrarError(mensaje) {
    zonaResultado.hidden = true;
    zonaError.hidden = false;
    mensajeError.textContent = mensaje;
}

function mostrarDiagnostico(d) {
    zonaError.hidden = true;
    zonaResultado.hidden = false;

    estadoGlobal.textContent = `Estado global: ${d.estado}`;

    listaParametros.innerHTML = "";
    for (const p of d.parametros) {
        const li = document.createElement("li");
        li.textContent = `${p.nombre}: ${p.valor} ${p.unidad} (rango ${p.rangoOptimo[0]}–${p.rangoOptimo[1]}) → ${p.estado}`;
        listaParametros.appendChild(li);
    }

    listaRecomendaciones.innerHTML = "";
    for (const r of d.recomendaciones) {
        const li = document.createElement("li");
        li.textContent = r;
        listaRecomendaciones.appendChild(li);
    }
}

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const cuerpo = {
        especie: selectorEspecie.value,
        humedad: parseFloat(document.getElementById("campo-humedad").value),
        luz: parseFloat(document.getElementById("campo-luz").value),
        temperatura: parseFloat(document.getElementById("campo-temperatura").value),
    };

    try {
        const respuesta = await fetch(`${URL_BASE_API}/diagnostics`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(cuerpo),
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            mostrarError(datos.mensaje || "Error desconocido");
            return;
        }

        mostrarDiagnostico(datos);
    } catch (error) {
        mostrarError("No se pudo conectar con el servidor.");
    }
});

cargarEspecies();