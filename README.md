# OBD-II Data Logger

Lee sensores del vehículo vía OBD-II y los almacena en CSV a través de una API REST.

```
[Raspberry Pi / PC con ELM327]  →  POST /obd/snapshot  →  [Servidor / Laptop]  →  data/obd_log.csv
          Cicloif.py                                            FastAPI (app/)
```

Ambos dispositivos deben estar en la misma red (o con IP accesible entre ellos).

---

## Requisitos

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) instalado en ambas máquinas
- Adaptador ELM327 (USB o Bluetooth) conectado a la máquina lectora

### Instalar UV

**Windows** (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux / Raspberry Pi**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Estructura del proyecto

```
Prueba-de-API/
├── app/
│   ├── main.py          # FastAPI: POST /obd/snapshot, GET /health
│   ├── schemas.py       # Modelos Pydantic (OBDRecord, OBDSnapshot)
│   └── csv_writer.py    # Escritura a CSV
├── obd/
│   └── Cicloif.py       # Lector OBD-II — corre en la máquina con el adaptador
├── data/
│   └── obd_log.csv      # Generado automáticamente al primer registro
├── pyproject.toml       # Dependencias (manejadas por UV)
└── uv.lock             # Lockfile — versiones exactas reproducibles
```

---

## Máquina 1 — Servidor API

Esta máquina recibe los datos y los guarda en CSV. Puede ser una laptop, PC o servidor.

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd Prueba-de-API
uv sync
```

### 2. Obtener la IP local

Necesitas esta IP para configurar la Raspberry Pi / máquina lectora.

**Windows:**
```powershell
ipconfig
# Busca "Dirección IPv4" bajo tu adaptador de red activo
```

**macOS:**
```bash
ipconfig getifaddr en0      # Wi-Fi
ipconfig getifaddr en1      # Ethernet (si aplica)
```

**Linux:**
```bash
ip a | grep "inet " | grep -v 127.0.0.1
```

### 3. Levantar la API

**Windows / macOS / Linux:**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> `--host 0.0.0.0` expone la API en la red local para que otros dispositivos puedan conectarse.

### 4. Verificar que funciona

**macOS / Linux:**
```bash
curl http://localhost:8000/health
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod http://localhost:8000/health
```

Respuesta esperada: `{"status":"ok"}`

La documentación interactiva (Swagger UI) está en:
`http://<IP-del-servidor>:8000/docs`

---

## Máquina 2 — Lector OBD-II (Raspberry Pi u otro equipo con ELM327)

Esta máquina se conecta al adaptador ELM327 y envía los datos al servidor.

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd Prueba-de-API
uv sync
```

### 2. Identificar el puerto serial del ELM327

**Windows:**
```powershell
# Abre el Administrador de dispositivos → Puertos (COM y LPT)
# O desde PowerShell:
Get-PnpDevice -Class Ports | Select-Object FriendlyName, Status
# Ejemplo de resultado: USB-SERIAL CH340 (COM9)
```

**macOS:**
```bash
ls /dev/tty.*
# Busca algo como: /dev/tty.usbserial-xxxx  o  /dev/tty.SLAB_USBtoUART
```

**Linux / Raspberry Pi:**
```bash
ls /dev/ttyUSB* /dev/ttyAMA*
# O para ver el puerto justo al conectar el adaptador:
dmesg | tail -20 | grep tty
```

### 3. Configurar puerto y URL de la API

Edita `obd/Cicloif.py` y ajusta las dos constantes al inicio:

```python
API_URL = "http://<IP-del-servidor>:8000/obd/snapshot"

# Windows:
PORT = "COM9"

# macOS:
PORT = "/dev/tty.usbserial-xxxx"

# Linux / Raspberry Pi:
PORT = "/dev/ttyUSB0"
```

### 4. Permisos del puerto serial (solo Linux / Raspberry Pi)

Si obtienes un error de permisos al abrir el puerto:

```bash
sudo usermod -aG dialout $USER
# Cierra sesión y vuelve a entrar para que tome efecto.
# Alternativa temporal sin reiniciar sesión:
sudo chmod a+rw /dev/ttyUSB0
```

### 5. Ejecutar el lector

```bash
uv run python obd/Cicloif.py
```

El script se conecta al vehículo, consulta todos los sensores soportados cada segundo y envía un snapshot a la API.

---

## Formato del CSV

El archivo `data/obd_log.csv` se crea automáticamente con las siguientes columnas:

| timestamp | command | value | unit |
|-----------|---------|-------|------|
| 2025-01-15T10:23:01.123Z | RPM | 850.0 | rpm |
| 2025-01-15T10:23:01.123Z | SPEED | 0.0 | kph |

---

## Endpoint de la API

### `POST /obd/snapshot`

Guarda un snapshot con múltiples lecturas de sensores.

**Body:**
```json
{
  "timestamp": "2025-01-15T10:23:01.123Z",
  "records": [
    { "command": "RPM",   "value": "850.0", "unit": "rpm" },
    { "command": "SPEED", "value": "0.0",   "unit": "kph" }
  ]
}
```

**Respuesta `201`:**
```json
{ "saved_records": 2, "timestamp": "2025-01-15T10:23:01.123Z" }
```

### `GET /health`

```json
{ "status": "ok" }
```

---

## Gestión de dependencias con UV

```bash
uv add <paquete>                 # agregar dependencia de producción
uv add --group dev <paquete>     # agregar dependencia de desarrollo
uv sync                          # instalar todo (producción)
uv sync --group dev              # instalar incluyendo dev (pytest, httpx)
```

El `uv.lock` debe commitearse al repositorio para garantizar instalaciones reproducibles en todos los sistemas operativos.
