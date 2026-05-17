# Diagnóstico de conexión con el Arduino
import sys
import time
import serial
from serial.tools import list_ports

# Forzar UTF-8 en stdout para que no explote con caracteres unicode en Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

print("-" * 50)
print("Puertos disponibles:")
for p in list_ports.comports():
    print(f"  {p.device:8}  {p.description}")
print("-" * 50)

PUERTO = "COM3"
print(f"\nAbriendo {PUERTO} a 9600 baudios...")
s = serial.Serial(PUERTO, 9600, timeout=1)

# El sketch principal hace una rampa lenta hacia PARKED en setup() antes
# de imprimir READY. Hay que darle tiempo (con MS_POR_PASO_INICIAL=200 y
# diff ~30°, son ~6-7 seg). Esperamos hasta 12 seg leyendo todo lo que llegue.
print("Esperando hasta 12s a que arranque el sketch (incluye rampa lenta)...")
print("\nLo que va mandando el Arduino:")
inicio = time.time()
ready_recibido = False
while time.time() - inicio < 12:
    if s.in_waiting > 0:
        linea = s.readline().decode("ascii", errors="replace").strip()
        if linea:
            print(f"  Arduino dice: '{linea}'")
            if linea == "READY":
                ready_recibido = True
                break
    else:
        time.sleep(0.1)

if not ready_recibido:
    print("\n[!] No llego READY en 12 seg. El sketch principal puede no estar cargado.")

print("\nMandando PING...")
s.reset_input_buffer()
s.write(b"PING\n")
s.flush()

print("Esperando PONG (5 segundos)...")
inicio = time.time()
pong_recibido = False
while time.time() - inicio < 5:
    if s.in_waiting > 0:
        linea = s.readline().decode("ascii", errors="replace").strip()
        if linea:
            print(f"  Arduino dice: '{linea}'")
            if linea == "PONG":
                print("\n[OK] CONEXION CORRECTA — sketch principal cargado y respondiendo")
                pong_recibido = True
                break

if not pong_recibido:
    print("\n[X] Sin respuesta a PING — el sketch principal NO esta cargado.")
    print("    Subi 'arduino/brazo_robotico/brazo_robotico.ino' al Arduino.")

s.close()
