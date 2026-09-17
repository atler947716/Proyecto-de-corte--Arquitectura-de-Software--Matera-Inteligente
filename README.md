# Matera Inteligente — Corte de Arquitectura

Backend en Flask que diagnostica el estado de una planta a partir de una medición
ambiental (humedad, luz, temperatura) y una especie. Front web estático que consume
la API de forma asíncrona.

## Requisitos

- Python 3.10 o superior
- pip
- Navegador web moderno

## Instalación

Desde la raíz del repositorio:

    pip install -r requirements.txt

## Ejecutar el backend

Desde la carpeta `backend/`:

    cd backend
    python App.py

El servidor queda escuchando en http://localhost:5000

En Codespaces, hacer público el puerto 5000 desde la pestaña "Puertos".

## Ejecutar el frontend

Desde la carpeta `frontend/`, en otra terminal:

    cd frontend
    python -m http.server 5510

Abrir en el navegador http://localhost:5510

En Codespaces, hacer público el puerto 5510 y abrir la URL pública.

## Ejecutar las pruebas del dominio

Desde la raíz del repositorio:

    pytest -v

Las 14 pruebas pasan sin levantar el servidor y sin leer el archivo CSV real.
Usan un doble de prueba del puerto `I_ProveedorDeRangos`.

## Endpoints

### POST /api/v1/diagnostics

Recibe una especie y tres parámetros. Devuelve el diagnóstico.

    {
      "especie": "Roble Andino (Quercus humboldtii)",
      "humedad": 50,
      "luz": 800,
      "temperatura": 18
    }

Respuesta 200 con el diagnóstico.

Errores:
- 404 si la especie no existe.
- 400 si falta un campo, no es numérico o está fuera del rango físico.

### GET /api/v1/especies

Devuelve la lista de especies soportadas con sus rangos de referencia.

## Estructura de capas

- `backend/dominio/` — entidades, evaluador y puerto. No depende de Flask, ni de CSV, ni de JSON.
- `backend/aplicacion/` — casos de uso que orquestan.
- `backend/infraestructura/` — implementación concreta del puerto.
- `backend/presentacion/` — controlador REST y objetos de transferencia de datos.

## Fuentes de los rangos

Los rangos de cada especie fueron tomados de fichas de jardinería y botánica
citadas en la columna `fuente` del archivo
`backend/infraestructura/recursos/especies.csv`.git add README.md
git commit -m "documentacion: instrucciones de ejecucion"