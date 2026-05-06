# OBD-II Data Logger

Sistema embebido para lectura continua de sensores vehiculares via OBD-II. Diseñado para correr en una Raspberry Pi conectada al puerto de diagnóstico del auto, exponiendo los datos a través de una API REST y guardándolos en CSV.

---

## Arquitectura

```
[ Auto / Puerto OBD-II ]
         │  USB
         ▼
[ ELM327 Adapter ]
         │  USB (/dev/ttyUSB0)
         ▼
[ Raspberry Pi ]
   ├── obd_collector.py  ← lee sensores cada segundo
   └── FastAPI (uvicorn) ← recibe y persiste los datos
         │
         ▼
   data/obd_log.csv
```

### Módulos

| Archivo | Descripción |
|---|---|
| `obd/obd_collector.py` | Lee sensores OBD-II y envía snapshots a la API |
| `app/main.py` | FastAPI: `POST /obd/snapshot`, `GET /health` |
| `app/schemas.py` | Modelos Pydantic: `OBDRecord`, `OBDSnapshot` |
| `app/csv_writer.py` | Persiste cada snapshot en `data/obd_log.csv` |

---

## Requisitos

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (gestor de dependencias)
- Adaptador ELM327 (USB o Bluetooth)

### Instalar UV

**macOS / Linux / Raspberry Pi:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `OBD_PORT` | `/dev/ttyUSB0` | Puerto serie del adaptador ELM327 |
| `OBD_API_URL` | `http://127.0.0.1:8000/obd/snapshot` | Endpoint donde se envían los snapshots |

---

## Instalación y ejecución local (desarrollo)

```bash
# 1. Clonar el repo
git clone <repo-url>
cd obd-data-logger

# 2. Instalar dependencias
uv sync

# 3. Terminal 1 — levantar la API
uv run uvicorn app.main:app --reload

# 4. Terminal 2 — iniciar la lectura OBD
OBD_PORT=/dev/ttyUSB0 uv run python obd/obd_collector.py
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva en `http://localhost:8000/docs`.

---

## Despliegue en Raspberry Pi

### 1. Preparar el sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-dev libffi-dev

# Instalar UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 2. Clonar el proyecto

```bash
git clone <repo-url> ~/obd-logger
cd ~/obd-logger
uv sync
```

### 3. Verificar el adaptador ELM327

```bash
# Conectar el ELM327 por USB y verificar que el sistema lo detecta
ls /dev/ttyUSB*          # ELM327 USB  → normalmente /dev/ttyUSB0
ls /dev/rfcomm*          # ELM327 Bluetooth (si ya está pareado)

# Ver el evento justo al conectar
dmesg | tail -20 | grep tty

# Dar permisos al usuario para acceder al puerto serie
sudo usermod -aG dialout $USER
# Cerrar sesión y volver a entrar para que tome efecto
# Alternativa temporal:
sudo chmod a+rw /dev/ttyUSB0
```

### 4. Configurar servicios systemd (arranque automático)

**Servicio de la API:**

```bash
sudo nano /etc/systemd/system/obd-api.service
```

```ini
[Unit]
Description=OBD Data Logger API
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/obd-logger
ExecStart=/home/pi/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Servicio del colector OBD:**

```bash
sudo nano /etc/systemd/system/obd-collector.service
```

```ini
[Unit]
Description=OBD Sensor Collector
After=network.target obd-api.service
Requires=obd-api.service

[Service]
User=pi
WorkingDirectory=/home/pi/obd-logger
Environment="OBD_PORT=/dev/ttyUSB0"
Environment="OBD_API_URL=http://127.0.0.1:8000/obd/snapshot"
ExecStart=/home/pi/.local/bin/uv run python obd/obd_collector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Habilitar y arrancar:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable obd-api obd-collector
sudo systemctl start obd-api obd-collector

# Verificar estado
sudo systemctl status obd-api
sudo systemctl status obd-collector

# Ver logs en tiempo real
sudo journalctl -fu obd-api
sudo journalctl -fu obd-collector
```

---

## Acceso desde otros dispositivos

### Opción A — Misma red local (WiFi/LAN)

Todos los dispositivos en el mismo router. La Raspberry Pi expone la API en su IP local.

**1. Obtener la IP de la Raspberry Pi:**

```bash
hostname -I
# Ejemplo: 192.168.1.42
```

**2. Asignar IP estática (recomendado para no tener que buscarla cada vez):**

```bash
sudo nano /etc/dhcpcd.conf
```

Agregar al final:

```
interface wlan0
static ip_address=192.168.1.42/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

```bash
sudo systemctl restart dhcpcd
```

**3. Acceder desde cualquier dispositivo en la red:**

```
http://192.168.1.42:8000/docs      ← documentación interactiva
http://192.168.1.42:8000/health    ← health check
```

**4. Si el colector corre en otro dispositivo de la misma red:**

```bash
OBD_API_URL=http://192.168.1.42:8000/obd/snapshot uv run python obd/obd_collector.py
```

---

### Opción B — Redes diferentes (acceso remoto)

#### B.1 — Tailscale (recomendado — gratis, sin tocar el router)

Tailscale crea una VPN mesh privada entre tus dispositivos. No requiere abrir puertos ni configurar el router.

```bash
# En la Raspberry Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Ver la IP de Tailscale asignada
tailscale ip -4
# Ejemplo: 100.94.12.33
```

Instalar Tailscale en tu laptop/teléfono desde [tailscale.com/download](https://tailscale.com/download) e iniciar sesión con la misma cuenta.

Acceso desde cualquier red:

```
http://100.94.12.33:8000/docs
```

En el colector (si corre en un dispositivo diferente de la red Tailscale):

```bash
OBD_API_URL=http://100.94.12.33:8000/obd/snapshot uv run python obd/obd_collector.py
```

> La Pi solo es accesible por dispositivos en tu cuenta de Tailscale — no queda expuesta al internet público.

---

#### B.2 — Cloudflare Tunnel (sin tocar el router, URL pública)

Útil si quieres compartir el acceso con alguien fuera de tu red sin darle acceso VPN.

```bash
# Instalar cloudflared en la Raspberry Pi (ARM64)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Crear un túnel temporal (pruebas — URL cambia cada reinicio)
cloudflared tunnel --url http://localhost:8000
# Genera una URL pública tipo: https://xyz.trycloudflare.com

# Para un túnel permanente, autenticarse con Cloudflare:
cloudflared tunnel login
cloudflared tunnel create obd-logger
```

---

#### B.3 — Port forwarding en el router

Si tienes acceso al router y una IP pública (o usas DDNS como Duck DNS):

1. En el router, crear una regla NAT/port forwarding: `puerto externo 8000 → IP de la Pi: 8000`
2. Obtener tu IP pública: `curl ifconfig.me`
3. Acceder desde fuera: `http://<ip-publica>:8000`

> **Precaución:** exponer la API directamente a internet sin autenticación es un riesgo de seguridad. Agrega autenticación o limita el acceso por IP antes de usar esta opción en producción.

---

## Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/obd/snapshot` | Guarda un snapshot de sensores |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Documentación Swagger interactiva |

### `POST /obd/snapshot`

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

---

## Formato del CSV

El archivo `data/obd_log.csv` se crea automáticamente:

| timestamp | command | value | unit |
|---|---|---|---|
| 2025-01-15T10:23:01Z | RPM | 850.0 | rpm |
| 2025-01-15T10:23:01Z | SPEED | 0.0 | kph |

---

## Estados de conexión OBD

| Estado | Descripción |
|---|---|
| `CAR_CONNECTED` | Comunicación completa — consulta todos los sensores soportados |
| `OBD_CONNECTED` | Adaptador detectado pero el auto no responde (motor apagado) |
| `ELM_CONNECTED` | Solo responde el chip ELM327, sin comunicación OBD |

---

## Gestión de dependencias con UV

```bash
uv sync                          # instalar dependencias de producción
uv sync --group dev              # instalar incluyendo dev (pytest, httpx)
uv add <paquete>                 # agregar dependencia de producción
uv add --group dev <paquete>     # agregar dependencia de desarrollo
```

El `uv.lock` debe commitearse al repositorio para garantizar instalaciones reproducibles.

---

## Estructura del proyecto

```
.
├── app/
│   ├── main.py          # FastAPI app
│   ├── schemas.py       # Modelos Pydantic
│   └── csv_writer.py    # Persistencia CSV
├── obd/
│   └── obd_collector.py # Lector OBD-II
├── data/
│   └── obd_log.csv      # Datos guardados (auto-creado)
├── pyproject.toml
└── uv.lock
```
