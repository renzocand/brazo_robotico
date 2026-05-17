"""
calibrar_casillas.py

Interactivo para calibrar casillas del tablero.

Flujo:
 - Calcula ángulos de servos para cada casilla usando `SistemaBrazo`.
 - Muestra los ángulos sugeridos y (opcional) los envía al Arduino con
   el comando `GOTO base,brazo1,brazo2` si `pyserial` está instalado y
   el usuario acepta.
 - Pide al usuario que confirme la casilla alcanzada (o corrija) y guarda
   un registro CSV `calibracion_casillas.csv` con: casilla_objetivo,servo_base,servo_brazo1,servo_brazo2,casilla_observada,timestamp

Uso:
  python calibrar_casillas.py

Requiere que el paquete `brazo_robotico` esté en el PYTHONPATH (ejecuta
desde la raíz del repo). La comunicación serial es opcional.
"""

import csv
import datetime
import sys
from pathlib import Path

from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.config import ARDUINO_PUERTO, ARDUINO_BAUDIOS, INVERTIR_FILAS_TABLERO

OUT_FILE = Path("calibracion_casillas.csv")


def generar_casillas(invertir: bool):
    cols = [chr(ord('A') + i) for i in range(8)]
    filas = list(range(1, 9))
    if invertir:
        filas = list(reversed(filas))
    casillas = [f + str(r) for f in cols for r in filas]
    return casillas


def intentar_serial():
    try:
        import serial
        return serial
    except Exception:
        return None


def enviar_a_arduino(serial_mod, puerto, baudios, sv_base, sv_b1, sv_b2):
    try:
        with serial_mod.Serial(puerto, baudios, timeout=2) as ser:
            linea = f"GOTO {int(sv_base)},{int(sv_b1)},{int(sv_b2)}\n"
            ser.write(linea.encode('ascii'))
            resp = ser.readline().decode('ascii', errors='ignore').strip()
            return resp
    except Exception as e:
        return f"ERROR: {e}"


def main():
    s = SistemaBrazo()
    serial_mod = intentar_serial()
    if serial_mod:
        print(f"pyserial disponible — puerto por defecto: {ARDUINO_PUERTO} @ {ARDUINO_BAUDIOS}")
    else:
        print("pyserial no encontrado — solo mostraré ángulos (no enviaré al Arduino).")

    casillas = generar_casillas(INVERTIR_FILAS_TABLERO)

    existe = OUT_FILE.exists()
    with OUT_FILE.open("a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not existe:
            writer.writerow(["timestamp", "casilla_objetivo", "servo_base", "servo_brazo1", "servo_brazo2", "casilla_observada"])

    for cas in casillas:
        coord = s.casilla_a_xyz(cas)
        ang = s.calcular_angulos(coord.x, coord.y)
        sv = s.angulos_a_servos(ang)

        print("\n---")
        print(f"Casilla objetivo: {cas}")
        print(f"  Coordenadas robot: x={coord.x:.1f} y={coord.y:.1f}")
        print(f"  Ángulos servos sugeridos: base={sv.base:.1f}, brazo1={sv.brazo1:.1f}, brazo2={sv.brazo2:.1f}")

        enviar = False
        if serial_mod:
            r = input("Enviar estos ángulos al Arduino? (y/N): ").strip().lower()
            if r == 'y':
                enviar = True
                resp = enviar_a_arduino(serial_mod, ARDUINO_PUERTO, ARDUINO_BAUDIOS, sv.base, sv.brazo1, sv.brazo2)
                print(f"Respuesta Arduino: {resp}")

        print("Prueba en el brazo: mueve y luego indica la casilla QUE REALMENTE alcanzó.")
        obs = input("Casilla observada (ENTER si fue correcta / 'skip' / 'quit'): ").strip().upper()
        if obs == 'QUIT':
            print("Terminando calibración por usuario.")
            break
        if obs == '':
            obs = cas
        if obs == 'SKIP':
            obs = ''

        with OUT_FILE.open("a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.datetime.utcnow().isoformat(), cas, f"{sv.base:.1f}", f"{sv.brazo1:.1f}", f"{sv.brazo2:.1f}", obs])

        print(f"Guardado: objetivo={cas} observada={obs}")

    print(f"Calibración finalizada. Archivo: {OUT_FILE.resolve()}")


if __name__ == '__main__':
    main()
