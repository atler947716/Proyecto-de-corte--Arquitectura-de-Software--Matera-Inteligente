
/* GreenMind — UI-01 a UI-09.
 * MODO DEMOSTRACIÓN: el backend publicado solo expone especies y diagnósticos.
 * Las cuentas, materas y lecturas de esta demo viven exclusivamente en este navegador.
 * No utilizar este modo para contraseñas reales ni datos sensibles.
 */
'use strict';

const BASE = (localStorage.getItem('matera_api_url') || 'http://localhost:5000/api/v1')
  .replace(/\/$/, '').replace(/\/api\/v1$/, '') + '/api/v1';
const $ = id => document.getElementById(id);
const DEMO_KEY = 'greenmind_demo_plantas_v1';
let plantas = leerDemo();
let seleccionada = null;
let sesionDemo = false;
let reloj = null;
let contadorLecturas = new Map();

function leerDemo() {
  try {
    const p = JSON.parse(localStorage.getItem(DEMO_KEY) || '[]');
    return Array.isArray(p) ? p : [];
  } catch {
    return [];
  }
}

function guardarDemo() {
  localStorage.setItem(DEMO_KEY, JSON.stringify(plantas));
}

function aviso(mensaje, error = false) {
  $('mensaje').textContent = mensaje;
  $('mensaje').style.color = error ? '#ff9b95' : '#76d9a5';
}

function navegar(id) {
  const nombres = ['inicio', 'materas', 'registrar-planta', 'detalle', 'perfil'];
  if (!nombres.includes(id)) return;
  nombres.forEach(n => $(n).hidden = n !== id);
  if (id === 'materas') renderPlantas();
  if (id === 'inicio') renderInicio();
}

function navegarAuth(id) {
  ['vista-login', 'vista-registro', 'vista-recuperar', 'vista-cambio-clave']
    .forEach(n => $(n).hidden = n !== id);
}

function mostrarSesion(activa) {
  sesionDemo = activa;
  $('auth').hidden = activa;
  $('panel').hidden = !activa;

  if (activa) {
    navegar('inicio');
    iniciarSimulacion();
  } else {
    clearInterval(reloj);
    reloj = null;
    navegarAuth('vista-login');
  }
}

const idNuevo = () => globalThis.crypto?.randomUUID?.() ||
  ('demo-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2));

const fecha = () => new Date().toISOString();

function numero(min, max) {
  return Math.round((Math.random() * (max - min) + min) * 10) / 10;
}

// Lecturas ilustrativas: una secuencia independiente por planta.
function generarLectura(p) {
  const i = (contadorLecturas.get(p.id) || 0) + 1;
  contadorLecturas.set(p.id, i);

  if (i % 11 === 0) return;

  const humedad = i % 7 === 0 ? 5 : numero(45, 65);

  const lectura = {
    fecha: fecha(),
    humedad,
    luz: numero(500, 1100),
    temperatura: numero(15, 23)
  };

  p.historial = [lectura, ...(p.historial || [])].slice(0, 30);
}

function iniciarSimulacion() {
  if (reloj !== null) clearInterval(reloj);

  reloj = setInterval(() => {
    if (!sesionDemo) return;

    plantas.forEach(generarLectura);
    guardarDemo();

    if (!$('detalle').hidden && seleccionada) mostrarDetalle();
    if (!$('inicio').hidden) renderInicio();
  }, 5000);
}

// =====================================
// CATÁLOGO DE ESPECIES
// =====================================

async function especies() {
  let nombres = [];

  try {
    const r = await fetch(`${BASE}/especies`, {
      signal: AbortSignal.timeout(3500)
    });

    if (!r.ok) throw new Error('No disponible');

    const datos = await r.json();

    nombres = datos
      .map(e => typeof e === 'string' ? e : e.nombre)
      .filter(Boolean);

  } catch {
    aviso(
      'API desconectada: el catálogo de especies necesita Flask.',
      true
    );
  }

  [$('especies'), $('editar-especie')].forEach(select => {
    select.replaceChildren();

    const vacia = document.createElement('option');
    vacia.value = '';
    vacia.textContent = 'Selecciona una especie';
    select.append(vacia);

    nombres.forEach(n => {
      const option = document.createElement('option');
      option.value = n;
      option.textContent = n;
      select.append(option);
    });
  });
}

// =====================================
// INVENTARIO DE PLANTAS
// =====================================

function renderPlantas() {
  const lista = $('plantas');
  lista.replaceChildren();

  if (plantas.length === 0) {
    const p = document.createElement('p');
    p.textContent = 'No hay plantas registradas en esta demostración.';
    lista.append(p);
    return;
  }

  plantas.forEach(p => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'planta';

    b.textContent = `${p.nombre} · ${p.especie} · ID: ${p.dispositivo}`;

    b.addEventListener('click', () => {
      seleccionada = p.id;
      navegar('detalle');
      mostrarDetalle();
    });

    lista.append(b);
  });
}

function renderInicio() {
  ['total-bien', 'total-regular', 'total-mal']
    .forEach(id => $(id).textContent = '0');

  $('total-sin-datos').textContent = String(plantas.length);

  $('alertas-inicio').textContent =
    'Sin alertas verificadas. Mediciones simuladas localmente.';

  $('cambios-inicio').textContent = plantas.some(p => p.historial?.length)
    ? 'Hay lecturas ilustrativas recientes. Consulta Mis materas.'
    : 'Todavía no existen lecturas.';
}

// =====================================
// MEDICIONES Y DIAGNÓSTICO
// =====================================

function ponerMedidas(lectura) {
  const zona = $('medidas');
  zona.replaceChildren();

  if (!lectura) return;

  [
    ['Humedad', lectura.humedad, '%'],
    ['Iluminación', lectura.luz, 'lux'],
    ['Temperatura', lectura.temperatura, '°C']
  ].forEach(([nombre, valor, unidad]) => {
    const div = document.createElement('div');
    const strong = document.createElement('strong');
    const dato = document.createElement('p');

    strong.textContent = nombre;
    dato.textContent = `${valor} ${unidad}`;

    div.append(strong, dato);
    zona.append(div);
  });
}

async function diagnosticoReal(p, lectura) {
  if (!lectura) return;

  const id = p.id;

  try {
    const r = await fetch(`${BASE}/diagnostics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        especie: p.especie,
        humedad: lectura.humedad,
        luz: lectura.luz,
        temperatura: lectura.temperatura
      }),
      signal: AbortSignal.timeout(3500)
    });

    if (!r.ok) {
      throw new Error('El diagnóstico no está disponible');
    }

    const datos = await r.json();

    if (seleccionada !== id || $('detalle').hidden) return;

    $('estado').textContent =
      `Diagnóstico API: ${datos.estado || 'No disponible'}`;

    const zona = $('recomendaciones');
    zona.replaceChildren();

    if (
      Array.isArray(datos.recomendaciones) &&
      datos.recomendaciones.length
    ) {
      const lista = document.createElement('ul');

      datos.recomendaciones.forEach(t => {
        const li = document.createElement('li');
        li.textContent = String(t);
        lista.append(li);
      });

      zona.append(lista);
    } else {
      zona.textContent = 'No hay recomendaciones disponibles.';
    }

  } catch {
    if (seleccionada === id) {
      $('estado').textContent =
        'No disponible (sin diagnóstico del servidor)';

      $('recomendaciones').textContent =
        'El diagnóstico requiere conexión con la API de Flask.';
    }
  }
}

function mostrarDetalle() {
  const p = plantas.find(x => x.id === seleccionada);
  if (!p) return;

  const lectura = p.historial?.[0];

  $('titulo').textContent = p.nombre;
  $('detalle-especie').textContent = `Especie: ${p.especie}`;
  $('detalle-identificador').textContent =
    `Dispositivo: ${p.dispositivo}`;

  $('estado').textContent =
    'No disponible (consultando diagnóstico)';

  $('fecha').textContent = lectura
    ? `Última lectura: ${new Date(lectura.fecha).toLocaleString('es-CO')}`
    : '';

  $('estado-datos').textContent = lectura
    ? 'Lectura ilustrativa del simulador local'
    : 'Sin lecturas';

  ponerMedidas(lectura);

  $('historial').replaceChildren();

  (p.historial || []).forEach(l => {
    const fila = document.createElement('p');

    fila.textContent =
      `${new Date(l.fecha).toLocaleString('es-CO')} · ` +
      `H ${l.humedad}% · ` +
      `L ${l.luz} lux · ` +
      `T ${l.temperatura}°C`;

    $('historial').append(fila);
  });

  if (!lectura) {
    $('historial').textContent =
      'Esperando primera lectura ilustrativa.';
  }

  $('recomendaciones').textContent = lectura
    ? 'Consultando reglas de la API…'
    : 'Esperando lecturas válidas.';

  diagnosticoReal(p, lectura);
}

// =====================================
// IDENTIFICACIÓN QR
// =====================================

function validarIdentificador() {
  const id = $('qr-manual').value.trim();

  if (!id) {
    return aviso('Introduce un identificador de matera.', true);
  }

  if (plantas.some(p => p.dispositivo === id)) {
    $('estado-qr').textContent =
      'Esta matera ya está vinculada en la demostración.';

    $('identificador-registro').value = '';
    return;
  }

  $('identificador-registro').value = id;

  $('estado-qr').textContent =
    'ID aceptado en modo demostración. ' +
    'La validación real requiere backend.';
}

function marcarNoDisponible(funcion) {
  aviso(
    `${funcion} requiere un endpoint seguro en el backend. ` +
    'No se efectuaron cambios.',
    true
  );
}

// =====================================
// EVENTOS E INTERACCIONES
// =====================================

document.addEventListener('DOMContentLoaded', async () => {

  // Navegación
  document.querySelectorAll('[data-pantalla]').forEach(b => {
    b.addEventListener('click', () => navegar(b.dataset.pantalla));
  });

  document.querySelectorAll('[data-auth-vista]').forEach(b => {
    b.addEventListener('click', () => navegarAuth(b.dataset.authVista));
  });

  // Mostrar u ocultar contraseñas
  document.querySelectorAll('.alternar-clave').forEach(c => {
    c.addEventListener('change', () => {
      c.dataset.objetivo.split(',').forEach(id => {
        if ($(id)) {
          $(id).type = c.checked ? 'text' : 'password';
        }
      });
    });
  });

  // Login demostrativo
  $('login').addEventListener('submit', e => {
    e.preventDefault();

    const email = new FormData(e.currentTarget).get('correo');

    $('perfil-correo').value = String(email || '');

    mostrarSesion(true);

    aviso(
      'MODO DEMOSTRACIÓN: ' +
      'no se ha iniciado sesión en el servidor.'
    );
  });

  // Cerrar sesión
  $('salir').addEventListener('click', () => {
    mostrarSesion(false);
    aviso('Demostración cerrada.');
  });

  // Registro de usuario
  $('registro').addEventListener('submit', e => {
    e.preventDefault();

    if (
      $('contrasena-registro').value !==
      $('confirmar-registro').value
    ) {
      return aviso('Las contraseñas no coinciden.', true);
    }

    marcarNoDisponible(
      'El registro de usuarios y la verificación por correo'
    );
  });

  // Recuperación de contraseña
  $('recuperar-contrasena').addEventListener('submit', e => {
    e.preventDefault();
    marcarNoDisponible('La recuperación de contraseña');
  });

  // Cambio de contraseña
  $('cambiar-contrasena').addEventListener('submit', e => {
    e.preventDefault();
    marcarNoDisponible('El cambio de contraseña');
  });

  [
    'verificar-cuenta',
    'reenviar-codigo',
    'solicitar-nuevo-codigo'
  ].forEach(id => {
    $(id).addEventListener('click', () => {
      marcarNoDisponible('La verificación por correo');
    });
  });

  // Perfil
  $('editar-perfil').addEventListener('submit', e => {
    e.preventDefault();
    marcarNoDisponible('La edición de perfil');
  });

  // Escaneo QR pendiente de integración
  $('activar-camara').addEventListener('click', () => {
    marcarNoDisponible('El escaneo QR con cámara');
  });

  $('reintentar-qr').addEventListener('click', () => {
    $('qr-manual').value = '';
    $('identificador-registro').value = '';

    $('estado-qr').textContent =
      'Esperando lectura del QR.';
  });

  $('validar-qr').addEventListener(
    'click',
    validarIdentificador
  );

  // Registrar planta en demostración local
  $('crear').addEventListener('submit', e => {
    e.preventDefault();

    const form = new FormData(e.currentTarget);

    const nombre =
      String(form.get('nombre') || '').trim();

    const especie =
      String(form.get('especie') || '').trim();

    const dispositivo =
      $('identificador-registro').value.trim();

    if (!dispositivo) {
      return aviso(
        'Valida el identificador antes de registrar.',
        true
      );
    }

    if (!nombre || !especie) {
      return aviso(
        'Nombre y especie son obligatorios.',
        true
      );
    }

    if (plantas.some(p => p.dispositivo === dispositivo)) {
      return aviso('Identificador ya vinculado.', true);
    }

    plantas.push({
      id: idNuevo(),
      nombre,
      especie,
      dispositivo,
      historial: []
    });

    guardarDemo();

    e.currentTarget.reset();

    $('identificador-registro').value = '';
    $('qr-manual').value = '';

    $('estado-qr').textContent =
      'Esperando lectura del QR.';

    navegar('materas');

    aviso(
      'Matera registrada SOLO en este navegador. ' +
      'Simulación ilustrativa activa.'
    );
  });

  // Abrir edición
  $('abrir-edicion').addEventListener('click', () => {
    const p = plantas.find(x => x.id === seleccionada);
    if (!p) return;

    $('editar-nombre').value = p.nombre;
    $('editar-especie').value = p.especie;
    $('editar-dispositivo').value = p.dispositivo;

    $('editar-planta').hidden = false;
  });

  // Cancelar edición
  $('cancelar-edicion').addEventListener('click', () => {
    $('editar-planta').hidden = true;
  });

  // Guardar edición local
  $('editar-planta').addEventListener('submit', e => {
    e.preventDefault();

    const p = plantas.find(x => x.id === seleccionada);
    if (!p) return;

    const nombre = $('editar-nombre').value.trim();
    const especie = $('editar-especie').value;

    if (!nombre || !especie) {
      return aviso(
        'Nombre y especie son obligatorios.',
        true
      );
    }

    p.nombre = nombre;
    p.especie = especie;

    guardarDemo();

    $('editar-planta').hidden = true;
    mostrarDetalle();

    aviso(
      'Cambios guardados SOLO en la demostración local.'
    );
  });

  // Abrir confirmación de desvinculación
  $('abrir-desvinculacion').addEventListener('click', () => {
    $('confirmar-desvinculacion').hidden = false;
  });

  $('cancelar-eliminacion').addEventListener('click', () => {
    $('confirmar-desvinculacion').hidden = true;
  });

  // Desvinculación local
  $('confirmar-eliminacion').addEventListener('click', () => {
    plantas = plantas.filter(p => p.id !== seleccionada);

    guardarDemo();
    seleccionada = null;

    $('confirmar-desvinculacion').hidden = true;

    navegar('materas');

    aviso(
      'Desvinculada SOLO en la demo. ' +
      'Archivo histórico real no implementado.'
    );
  });

  // Cambiar contraseña desde perfil
  $('perfil-cambiar-clave').addEventListener('click', () => {
    $('panel').hidden = true;
    $('auth').hidden = false;

    navegarAuth('vista-cambio-clave');
  });

  await especies();

  renderInicio();

  aviso(
    'Vista previa local. ' +
    'El backend publicado solo incluye diagnóstico y especies.'
  );
});
