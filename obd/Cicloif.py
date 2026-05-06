import obd

connection = (obd.OBD(portstr="COM9"))

if connection.status() == obd.OBDStatus.CAR_CONNECTED:
    print(f"Carro conectado correctamente")
    print(f"Estado:", connection.status())
    print(f"Protocolo:", connection.protocol_name())
    print(f"ID Protocolo:", connection.protocol_id())

    for cmd in connection.supported_commands:   #Este ciclo for nos regresará un valor en la variable cmd que impprimira los posibles codigos
        response = connection.query(cmd)
        if not response.is_null():
            print(f"{cmd.name}: {response.value}")
        else:
            print(f"Error en {cmd.name}")

elif connection.status() == obd.OBDStatus.OBD_CONNECTED:
    print("Adaptador conectado, pero el carro no responde.")
    print("   → Verifica que el motor esté encendido.")

elif connection.status() == obd.OBDStatus.ELM_CONNECTED:
    print("Solo el ELM327 responde, sin comunicación OBD.")

else:
    print("Sin conexión.")