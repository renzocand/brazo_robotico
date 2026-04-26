# Diagnóstico de conexión con el Arduino
import time
import serial
from serial.tools import list_ports

print("-" * 50)
print("Puertos disponibles:")
for p in list_ports.comports():
    print(f"  {p.device:8}  {p.description}")
print("-" * 50)

PUERTO = "COM4"
print(f"\nAbriendo {PUERTO} a 9600 baudios...")
s = serial.Serial(PUERTO, 9600, timeout=1)
print("Esperando 3s a que arranque el sketch...")
time.sleep(3)

print("\nLeyendo lo que mandó el Arduino al arrancar:")
while s.in_waiting > 0:
    linea = s.readline().decode("ascii", errors="replace").strip()
    print(f"  Arduino dice: '{linea}'")

print("\nMandando PING...")
s.reset_input_buffer()
s.write(b"PING\n")
s.flush()

print("Esperando respuesta (3 segundos)...")
inicio = time.time()
while time.time() - inicio < 3:
    if s.in_waiting > 0:
        linea = s.readline().decode("ascii", errors="replace").strip()
        print(f"  Arduino dice: '{linea}'")
        if linea == "PONG":
            print("\n[OK] CONEXION CORRECTA")
            break
else:
    print("\n✗ Sin respuesta a PING — el sketch puede no estar cargado o estar mal")

s.close()
