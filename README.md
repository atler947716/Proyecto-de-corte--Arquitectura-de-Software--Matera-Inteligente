# Matera Inteligente — Corte de Arquitectura

Aplicación web de monitoreo de plantas con backend **Flask (Python)**, frontend **HTML/CSS/JavaScript**, almacenamiento **SQLite** y simulador de un dispositivo **ESP32** por HTTP. El sistema maneja usuarios, materas vinculadas, lecturas de humedad/luz/temperatura, diagnósticos según especie y autenticación mediante **JWT**.

> Esta guía está preparada principalmente para **Windows 10/11 con PowerShell y VS Code**. No se necesita un ESP32 físico ni Node.js para ejecutar la aplicación. Las instrucciones suponen que los cambios del proyecto se han subido a GitHub; de lo contrario, un clon solo tendrá la versión publicada.

## 1. Requisitos previos

- **Git** instalado y disponible desde la terminal (`git --version`).
- **Python 3.10 o superior**, con `pip` y soporte para `venv` (`python --version`). Recomendado Python 3.11.
- **VS Code** (opcional) y un navegador actualizado.
- Conexión a Internet para clonar el proyecto e instalar las dependencias la primera vez.

La base de datos SQLite viene integrada en Python; no es necesario instalar un servidor de base de datos. Tampoco es necesario instalar Node.js ni hardware ESP32.

## 2. Descargar el proyecto en otro computador

Abre PowerShell en el directorio donde quieras guardar el proyecto:

```powershell
git clone https://github.com/atler947716/Proyecto-de-corte--Arquitectura-de-Software--Matera-Inteligente.git
cd Proyecto-de-corte--Arquitectura-de-Software--Matera-Inteligente
```

Opcional, para abrirlo en VS Code:

```powershell
code .
```

> Si `code` no está disponible, abre VS Code manualmente y elige **Archivo → Abrir carpeta**.

Para futuras actualizaciones del proyecto, desde esta misma carpeta:

```powershell
git pull origin main
```

## 3. Crear el entorno virtual `.venv`

Desde la **raíz del repositorio** (la carpeta que contiene `requirements.txt`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell impide activar el entorno, ejecuta **solo en esta terminal**:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Otra opción, sin activar el entorno virtual, es ejecutar Python directamente con `.\.venv\Scripts\python.exe`; reemplaza ese comando por `.\.venv\Scripts\python.exe` al usarlo.

Con el entorno activado, la terminal debería mostrar `(.venv)` al principio de la línea.

Instala las dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

El archivo `requirements.txt` incluye **Flask**, **Flask-Cors**, **PyJWT** y **pytest**. Los módulos `sqlite3`, `urllib`, `argparse`, `json` y `venv` vienen con Python.

Comprueba que las dependencias principales se cargan:

```powershell
python -c "import flask, flask_cors, jwt, pytest; print('Dependencias instaladas correctamente')"
```

## 4. Configurar el backend

El servidor exige definir la variable de entorno **`GREENMIND_JWT_SECRET`**, con **al menos 32 caracteres**. Sin ella Flask no inicia. El secreto debe ser privado y debe mantenerse igual entre reinicios para que los JWT emitidos previamente sigan siendo válidos.

**En la terminal PowerShell donde vas a iniciar Flask**, puedes generar una clave local aleatoria y guardarla en un archivo que no subas a GitHub:

```powershell
if (-not (Test-Path .greenmind-jwt-secret)) {
    $clave = python -c "import secrets; print(secrets.token_urlsafe(48))"
    Set-Content -Path .greenmind-jwt-secret -Value $clave -NoNewline
}
$env:GREENMIND_JWT_SECRET = (Get-Content .greenmind-jwt-secret -Raw).Trim()
```

**Antes de usar este archivo, añade `.greenmind-jwt-secret` a `.gitignore`** si aún no está. Nunca publiques el secreto, contraseñas, tokens o bases de datos de desarrollo.

Configura la ruta de la base de datos de usuarios, materas y lecturas:

```powershell
$env:GREENMIND_DB = "backend/data/greenmind_desarrollo.sqlite3"
```

La base se crea cuando se inicia la aplicación. **Cada computador tendrá sus propios usuarios y lecturas**: el repositorio no distribuye bases SQLite, cuentas ni claves de otros equipos.

Selecciona el proveedor de rangos por especie (valor predeterminado: CSV):

```powershell
$env:REFERENCE_BACKEND = "csv"
```

Opciones:

| Valor | Fuente de los rangos por especie |
|---|---|
| `csv` | `backend/infraestructura/recursos/especies.csv` |
| `db` | SQLite de rangos: `backend/data/rangos.sqlite3` (adaptador de rangos) |

**Importante:** `REFERENCE_BACKEND` cambia el origen de los *rangos de diagnóstico*, no la base SQLite de usuarios e historiales. Esa otra base la controla `GREENMIND_DB`.

## 5. Arrancar GreenMind

Con el entorno activado y las variables anteriores definidas, inicia Flask **desde la raíz del repositorio**:

```powershell
python backend/App.py
```

Abre en el navegador:

**http://127.0.0.1:5000/**

Flask ya sirve el archivo `frontend/index.html` y sus recursos estáticos, por lo que **no es necesario arrancar otro servidor para el frontend**. La interfaz se comunica con la API mediante solicitudes asíncronas y consulta periódicamente las lecturas.

Mantén esta terminal abierta. Para detener Flask utiliza **Ctrl+C**.

### Primer uso

1. En la página, selecciona **Crear una cuenta**.
2. Registra un correo y una contraseña de al menos ocho caracteres.
3. Inicia sesión.
4. En **Mis materas**, registra una planta e introduce su identificador de dispositivo (por ejemplo, `ESP32-TEST-001`).
5. Selecciona una especie de la lista.
6. Inicia el simulador siguiendo la sección siguiente.

No es necesario disponer de una cámara ni de un QR físico para la demostración: el formulario incluye la introducción manual del identificador.

## 6. Simulador ESP32: enviar mediciones a Flask

**Abre una segunda terminal PowerShell**, situada en la raíz del proyecto. La primera debe seguir ejecutando Flask.

Activa su entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

El simulador está en `simulador_esp32.py`. Genera lecturas periódicas independientes para cada dispositivo, incluyendo valores normales, fuera de rango y datos inválidos de prueba.

### Autenticación del dispositivo

Cada dispositivo necesita **su propio JWT con permiso `readings:write`**. No uses el JWT de inicio de sesión del usuario para enviar lecturas. Tampoco basta con conocer el identificador del dispositivo.

Si el backend incorpora el endpoint autenticado `POST /api/v1/plantas/<planta_id>/credencial`, puedes configurar una matera desde la segunda terminal:

```powershell
python configurar_simulador.py
```

Introduce el correo, contraseña e identificador del dispositivo que pertenece a tu cuenta. El script guarda el JWT en `tokens_dispositivos.json` sin imprimirlo. El archivo es privado y está ignorado por Git.

**Compatibilidad:** algunas versiones publicadas del backend pueden no incluir todavía esa ruta y responder `HTTP 404`. En ese caso, comprueba que los cambios locales estén publicados en GitHub y que Flask se haya reiniciado con la versión correcta. El endpoint de registro de planta también puede emitir `token_dispositivo` en su respuesta; esa credencial es otra fuente válida, pero no debes publicarla.

También puedes configurar manualmente `tokens_dispositivos.json` (si cuentas con JWT válidos emitidos para cada dispositivo):

```json
{
  "ESP32-TEST-001": "JWT_REAL_DEL_DISPOSITIVO_001",
  "ESP32-TEST-002": "JWT_REAL_DEL_DISPOSITIVO_002"
}
```

Los textos `JWT_REAL_...` son marcadores de posición, **no tokens funcionales**.

### Ejecutar un dispositivo

```powershell
python simulador_esp32.py --dispositivo ESP32-TEST-001 --intervalo 5
```

### Ejecutar varios dispositivos a la vez

```powershell
python simulador_esp32.py --dispositivos ESP32-TEST-001 ESP32-TEST-002 --intervalo 5
```

### Ejecutar solo 12 ciclos de prueba

```powershell
python simulador_esp32.py --dispositivo ESP32-TEST-001 --intervalo 5 --cantidad 12
```

### Opciones del simulador

| Opción | Uso |
|---|---|
| `--dispositivo ID` | Simular un dispositivo |
| `--dispositivos ID1 ID2 ...` | Simular varios dispositivos |
| `--intervalo 5` | Segundos de espera entre ciclos (predeterminado: 5) |
| `--cantidad 12` | Número de ciclos; `0` significa ejecución continua |
| `--api URL` | Dirección del backend; predeterminado `http://127.0.0.1:5000` |
| `--tokens RUTA` | Archivo JSON con JWT de dispositivos |
| `--token JWT` | JWT directo, solo para un dispositivo; evita usarlo en comandos compartidos |

**Advertencia sobre `DEVICE_TOKEN`:** si una terminal conserva esa variable con un JWT viejo, puede prevalecer sobre el archivo JSON. Puedes quitarla temporalmente con:

```powershell
Remove-Item Env:DEVICE_TOKEN -ErrorAction SilentlyContinue
```

### Respuestas esperadas

- **HTTP 201:** lectura válida almacenada.
- **HTTP 400:** lectura con un dato inválido; es un caso de prueba esperado (por ejemplo, humedad no numérica).
- **HTTP 401:** JWT ausente, inválido o vencido; revisa credenciales y el secreto del servidor.
- **HTTP 403:** permisos insuficientes o token correspondiente a otro dispositivo.
- **HTTP 404:** dispositivo no vinculado a una matera activa o ruta no disponible.
- **Sin conexión:** verifica que Flask siga ejecutándose en el puerto configurado.

La lectura `FUERA_DE_RANGO` puede guardarse normalmente con HTTP 201: su valor es numérico y válido como dato físico, aunque no sea saludable para la planta. Las lecturas deliberadamente inválidas deben ser rechazadas.

Para detener el simulador, pulsa **Ctrl+C**.

## 7. Ejecutar las pruebas

En otra terminal, con el entorno activado y desde la raíz:

```powershell
python -m pytest -v
```

Para comprobar sintaxis de los módulos Python:

```powershell
python -m compileall -q backend
```

Las pruebas unitarias del dominio deben poder ejecutarse sin iniciar el servidor Flask. Si falla una prueba, consulta su error; no presupongas que todas pasan solo porque la aplicación arranca.

## 8. Demostración del cambio CSV ↔ SQLite

Detén Flask con **Ctrl+C**. En la terminal del servidor cambia únicamente la variable:

```powershell
$env:REFERENCE_BACKEND = "db"
python backend/App.py
```

Verifica que la API y el diagnóstico respondan correctamente. Para volver a CSV:

```powershell
$env:REFERENCE_BACKEND = "csv"
python backend/App.py
```

El objetivo es cambiar de adaptador sin modificar el código del dominio. La fuente SQLite de rangos es distinta de la base que contiene usuarios, materas y lecturas.

## 9. Estructura principal

```text
.
├── backend/
│   ├── App.py                         # Inicialización y composición Flask
│   ├── aplicacion/                    # Casos de uso
│   ├── dominio/                       # Modelos, reglas y puertos
│   ├── infraestructura/               # Adaptadores CSV y SQLite
│   │   └── recursos/especies.csv
│   ├── presentacion/                  # Endpoints REST y seguridad JWT
│   └── data/                          # SQLite local: ignorado por Git
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── estilo.css
├── simulador_esp32.py                # Simulador HTTP
├── configurar_simulador.py           # Obtención local de JWT de dispositivo
├── requirements.txt
└── README.md
```

### API principal

| Método y ruta | Función |
|---|---|
| `POST /api/auth/register` | Crear cuenta |
| `POST /api/auth/login` | Iniciar sesión y obtener JWT de usuario |
| `GET /api/auth/perfil` | Consultar perfil *(si el cambio está incorporado)* |
| `PATCH /api/auth/perfil` | Actualizar nombre *(si está incorporado)* |
| `DELETE /api/auth/perfil` | Eliminar cuenta, materas e historial *(si está incorporado)* |
| `GET /api/v1/especies` | Consultar especies y rangos |
| `POST /api/v1/diagnostics` | Diagnóstico por valores enviados |
| `GET /api/v1/plantas` | Listar las plantas del usuario |
| `POST /api/v1/plantas` | Registrar una matera |
| `PATCH /api/v1/plantas/<id>` | Modificar una planta |
| `DELETE /api/v1/plantas/<id>` | Desvincular una planta |
| `GET /api/v1/plantas/<id>/estado` | Estado y última lectura |
| `GET /api/v1/plantas/<id>/historial` | Historial de lecturas |
| `POST /api/v1/plantas/<id>/credencial` | Emitir JWT de dispositivo *(si está incorporado)* |
| `POST /api/dispositivos/<id>/lecturas` | Recibir lectura con JWT de dispositivo |

Los endpoints protegidos requieren `Authorization: Bearer <JWT>` con el alcance correspondiente.

## 10. Problemas frecuentes

**`python` no se reconoce:** instala Python y habilita el lanzador/entrada al PATH; también puedes probar `py -3 --version` y `py -3 -m venv .venv`.

**No se puede activar `.venv`:** usa `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, luego repite la activación. No necesitas cambiar la política del sistema entero.

**`ModuleNotFoundError: No module named flask` o `jwt`:** activa `.venv` e instala con `python -m pip install -r requirements.txt`.

**`GREENMIND_JWT_SECRET debe tener al menos 32 caracteres`:** define esa variable en la misma terminal que ejecuta Flask y conserva la clave usada anteriormente.

**`HTTP 401 Token inválido o vencido`:** renueva el JWT del dispositivo y comprueba que el servidor use el mismo secreto con el que lo emitió. Cada dispositivo tiene token independiente.

**`HTTP 403` en GitHub al hacer `git push`:** la cuenta autenticada carece de permisos para escribir en el repositorio. Esto no impide ejecutar GreenMind en otro computador.

**`HTTP 404` en `/credencial`:** el backend que está corriendo no incluye esa ruta; comprueba la versión del código y reinicia Flask.

**`database disk image is malformed` o error de esquema SQLite:** no sustituyas una base vieja por otra ni borres datos sin respaldo. En una instalación nueva usa una ruta SQLite nueva mediante `GREENMIND_DB`.

**El puerto 5000 está ocupado:** cierra el Flask anterior que sigue ejecutándose antes de arrancar uno nuevo.

**La página no actualiza las lecturas:** asegúrate de que Flask y el simulador estén activos, que la matera registrada tenga el mismo ID que el simulador y que la consola indique HTTP 201.

## 11. Seguridad y buenas prácticas

- No publiques `GREENMIND_JWT_SECRET`, archivos `.env`, JWT, `tokens_dispositivos.json`, bases `.sqlite3` ni copias de seguridad.
- En una instalación nueva, cada persona debe crear su propia cuenta y dispositivos.
- No utilices el servidor de desarrollo de Flask (`debug=True`) en Internet o producción. Es exclusivamente para desarrollo y demostraciones locales.
- Eliminar una cuenta de la aplicación no elimina copias de seguridad externas.
- El sistema actualmente usa lecturas simuladas y **no** necesita hardware real.

## 12. Para entregar y sustentar el corte 2

Asegúrate de poder demostrar en otro equipo: registro/login, propiedad y aislamiento de materas, JWT de usuario/dispositivo, lecturas del simulador en vivo, rechazo de datos inválidos, historial persistente, actualización del frontend, cambio CSV/BD por configuración y pruebas unitarias del dominio.

El **documento de arquitectura** debe ser redactado y comprendido por los integrantes del equipo conforme al enunciado; no se sustituye por este README.

Los rangos de cada especie fueron tomados de fichas de jardinería y botánica
citadas en la columna `fuente` del archivo
`backend/infraestructura/recursos/especies.csv`.git add README.md
git commit -m "documentacion: instrucciones de ejecucion"
