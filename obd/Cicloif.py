import obd
import time
import requests
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000/obd/snapshot"
PORT = "COM9"  # Cambia a /dev/ttyUSB0 en Linux/Mac

connection = obd.OBD(portstr=PORT)


def _build_payload(data: dict) -> dict:
    records = []
    ts = datetime.now(timezone.utc).isoformat()
    for name, response_value in data.items():
        magnitude = response_value
        unit = None
        if hasattr(response_value, "magnitude"):
            unit = str(response_value.units) if hasattr(response_value, "units") else None
            magnitude = response_value.magnitude
        records.append({
            "timestamp": ts,
            "command": name,
            "value": str(magnitude),
            "unit": unit,
        })
    return {"timestamp": ts, "records": records}


def _post_snapshot(data: dict) -> None:
    if not data:
        return
    try:
        payload = _build_payload(data)
        response = requests.post(API_URL, json=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"[API] {result['saved_records']} registros guardados.")
    except requests.RequestException as exc:
        print(f"[API] Error al enviar datos: {exc}")


def scan_obd() -> dict:
    data = {}
    try:
        status = connection.status()

        if status == obd.OBDStatus.CAR_CONNECTED:
            print("Carro conectado correctamente")
            print("Estado:", status)
            print("Protocolo:", connection.protocol_name())
            print("ID Protocolo:", connection.protocol_id())

            for cmd in connection.supported_commands:
                response = connection.query(cmd)
                if not response.is_null():
                    print(f"{cmd.name}: {response.value}")
                    data[cmd.name] = response.value
                else:
                    print(f"Sin datos: {cmd.name}")

        elif status == obd.OBDStatus.OBD_CONNECTED:
            print("Adaptador conectado, pero el carro no responde.")
            print("   → Verifica que el motor esté encendido.")

        elif status == obd.OBDStatus.ELM_CONNECTED:
            print("Solo el ELM327 responde, sin comunicación OBD.")

        else:
            print("Sin conexión.")

    except Exception as exc:
        print(f"Error al leer OBD: {exc}")

    return data


def main():
    while True:
        data = scan_obd()
        print("Datos recopilados:", data)
        _post_snapshot(data)
        time.sleep(1)


if __name__ == "__main__":
    main()
