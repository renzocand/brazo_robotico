"""
Herramienta interactiva para calibrar el mapeo casilla -> servos del brazo.

Uso:
    1. Subi brazo_robotico.ino al Arduino (con el comando GOTO agregado).
    2. python calibrar_tablero.py
    3. Por cada celda objetivo:
       - Tipeas la casilla (ej: E5).
       - El brazo va y se queda quieto (sin pinza, sin volver a parked).
       - Observas fisicamente sobre que casilla cayo la pinza.
       - Tipeas la casilla real (ej: D6).
    4. Cuando tengas 2+ puntos, comando 'a' para analisis + sugerencias.
    5. Ajustas config.py segun lo sugerido y volves a probar.

Comandos en el prompt principal:
    casilla     atajo: tipear directamente una casilla (ej E5) la mueve
    m / Enter   mover el brazo a una casilla y registrar resultado
    h           HOME (volver a parked)
    z           setear z_offset (cm bajo el plano del tablero) — default -3
    l           listar pares registrados
    a           analizar pares y sugerir cambios de config
    t           dibujar el tablero (referencia del robot)
    q           salir
"""
import math
import sys

from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.arduino_link import ArduinoLink
from brazo_robotico.config import (
    ARDUINO_PUERTO,
    ARDUINO_BAUDIOS,
    DIAMETRO_CASILLA,
    OFFSET_BRAZO,
    SERVO_BASE_OFFSET,
    LARGO_PRIMER_BRAZO,
    LARGO_SEGUNDO_BRAZO,
    INVERTIR_FILAS_TABLERO,
)


# Forzar UTF-8 en stdout para que no explote con caracteres unicode en Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    print()
    print("=" * 60)
    print("  CALIBRADOR DE TABLERO - Brazo Robotico")
    print("=" * 60)
    print()

    sistema = SistemaBrazo()
    arduino = ArduinoLink(puerto=ARDUINO_PUERTO, baudios=ARDUINO_BAUDIOS)

    print(f"Conectando con el Arduino en {ARDUINO_PUERTO}...")
    try:
        arduino.conectar()
    except Exception as e:
        print(f"  ERROR conectando: {e}")
        print("  Verifica que el sketch este cargado y el Serial Monitor cerrado.")
        return

    if not arduino.ping():
        print("  ERROR: el Arduino no respondio a PING.")
        print("  Subi brazo_robotico.ino al Arduino y volve a probar.")
        arduino.cerrar()
        return
    print("  Arduino conectado y respondiendo. OK.")
    print()

    pares = []   # list[(target_str, actual_str, target_xyz, actual_xyz)]

    # z_offset: cuanto baja la pinza por DEBAJO del plano nominal del tablero (z=0).
    # Negativo = pinza apunta mas abajo, asi efectivamente toca/se acerca al tablero.
    # Si es 0, la cinematica calcula angulos que dejan la pinza FLOTANDO sobre el
    # tablero (a la altura de la base del brazo, segun z=0). En la realidad el
    # tablero suele estar un poco mas abajo que la base, por eso conviene -2/-4.
    z_offset = -3.0

    # Aseguramos que arrancamos en parked, asi el primer movimiento sale
    # desde una posicion conocida.
    print("Posicionando brazo en HOME antes de empezar...")
    arduino.home()
    print()

    # Mostrar el tablero de referencia al arrancar.
    dibujar_tablero(z_offset=z_offset)

    try:
        while True:
            cmd = input(
                f"\n[casilla / m / h=home / z (z={z_offset:+.1f}) / l / a / t / q]: "
            ).strip().lower()

            if cmd in ("q", "quit", "exit"):
                break
            elif cmd == "h":
                print("  Mandando HOME...")
                resp = arduino.home()
                print(f"  Arduino: {resp or '(sin respuesta)'}")
            elif cmd == "l":
                listar_pares(pares)
            elif cmd == "a":
                analizar(pares)
            elif cmd == "t":
                dibujar_tablero(z_offset=z_offset)
            elif cmd == "z":
                z_offset = pedir_z_offset(z_offset)
            elif cmd in ("m", ""):
                target = input("  Casilla objetivo (ej E5): ").strip().upper()
                mover_y_registrar(sistema, arduino, pares, target, z_offset)
            elif _es_casilla(cmd):
                # Atajo: tipear directamente la casilla.
                mover_y_registrar(sistema, arduino, pares, cmd.upper(), z_offset)
            else:
                print(f"  Comando desconocido: '{cmd}'")
    finally:
        print("\nCerrando conexion...")
        arduino.cerrar()


def pedir_z_offset(actual: float) -> float:
    print(f"  z_offset actual: {actual:+.1f} cm  (negativo = pinza mas abajo)")
    print( "  Sugerencias: 0 = plano del tablero (tipico flotante)")
    print( "               -2 a -4 = la pinza efectivamente toca el tablero")
    nuevo_str = input("  Nuevo z_offset (cm) o Enter para no cambiar: ").strip()
    if not nuevo_str:
        return actual
    try:
        nuevo = float(nuevo_str)
    except ValueError:
        print("  Valor invalido, no se cambia.")
        return actual
    print(f"  z_offset cambiado a {nuevo:+.1f} cm")
    return nuevo


def _es_casilla(s: str) -> bool:
    """Devuelve True si s parece una casilla del tablero (ej 'E5', 'b3')."""
    if len(s) != 2:
        return False
    return s[0].isalpha() and s[1].isdigit()


def dibujar_tablero(target=None, actual=None, z_offset=None):
    """
    Dibuja el tablero 8x8 visto desde arriba con la referencia que usa el robot.

    Convenciones (las mismas que SistemaBrazo.casilla_a_xyz):
      - El brazo esta en el origen (0, 0). Se dibuja DEBAJO del tablero.
      - El tablero arranca a OFFSET_BRAZO cm en +Y.
      - Fila 1 = la mas CERCANA al brazo (abajo en el dibujo).
      - Fila 8 = la mas LEJOS del brazo (arriba en el dibujo).
      - Columna A esta en X negativo (izquierda); columna H en X positivo (derecha).

    Si pasas `target` (ej "E5") y/o `actual` (ej "D6"), las marca en el tablero:
      [T]=target, [A]=actual, [*]=ambas son la misma.
    """
    target = (target or "").upper()
    actual = (actual or "").upper()

    ancho_tablero = 8 * DIAMETRO_CASILLA
    alcance_max = LARGO_PRIMER_BRAZO + LARGO_SEGUNDO_BRAZO

    # Orden visual: las filas se dibujan de "lejos" arriba a "cerca" abajo.
    # Si INVERTIR_FILAS_TABLERO=True: fila 1 esta lejos, fila 8 cerca.
    # Si False (default chess): fila 8 esta lejos, fila 1 cerca.
    if INVERTIR_FILAS_TABLERO:
        orden_filas = list(range(1, 9))   # arriba=1 (lejos), abajo=8 (cerca)
    else:
        orden_filas = list(range(8, 0, -1))  # arriba=8 (lejos), abajo=1 (cerca)

    print()
    print("  +-- TABLERO (vista desde arriba) ----------------------+")
    print(f"  |  Config: DIAMETRO_CASILLA={DIAMETRO_CASILLA}cm  OFFSET_BRAZO={OFFSET_BRAZO}cm  |")
    print(f"  |          tablero {ancho_tablero:.0f}x{ancho_tablero:.0f}cm   alcance brazo {alcance_max:.1f}cm        |")
    if z_offset is not None:
        print(f"  |  z_offset = {z_offset:+.1f} cm (negativo = pinza apunta mas abajo)  |")
    print(f"  |  INVERTIR_FILAS_TABLERO = {INVERTIR_FILAS_TABLERO}                   |")
    print("  +------------------------------------------------------+")
    print()
    print("           A   B   C   D   E   F   G   H        (lejos)")
    print("         +---+---+---+---+---+---+---+---+")

    for idx, fila in enumerate(orden_filas):
        line = f"     {fila}   |"
        for col_idx in range(8):
            col_letter = chr(ord('A') + col_idx)
            casilla = f"{col_letter}{fila}"
            if casilla == target and casilla == actual:
                cell = "[*]"
            elif casilla == target:
                cell = "[T]"
            elif casilla == actual:
                cell = "[A]"
            else:
                cell = "   "
            line += cell + "|"
        print(line)
        if idx < len(orden_filas) - 1:
            print("         +---+---+---+---+---+---+---+---+")

    print("         +---+---+---+---+---+---+---+---+        (cerca)")
    print("           A   B   C   D   E   F   G   H")
    print()
    print(f"                          ↑ {OFFSET_BRAZO} cm (OFFSET_BRAZO)")
    print( "                       [BRAZO]  (origen 0,0)")
    print( "                      X-       X+")
    print()

    if target or actual:
        leyenda = []
        if target and target == actual:
            leyenda.append(f"[*] = {target} (objetivo y llegada coinciden)")
        else:
            if target:
                leyenda.append(f"[T] = {target} (objetivo)")
            if actual:
                leyenda.append(f"[A] = {actual} (donde llego)")
        for linea in leyenda:
            print(f"     {linea}")
        print()


def mover_y_registrar(sistema, arduino, pares, target, z_offset=0.0):
    target = (target or "").strip().upper()
    if len(target) != 2:
        print("  Casilla invalida (formato: letra A-H + numero 1-8).")
        return

    try:
        coord = sistema.casilla_a_xyz(target)
    except ValueError as e:
        print(f"  Casilla invalida: {e}")
        return

    z_calibracion = coord.z + z_offset

    if not sistema.es_alcanzable(coord.x, coord.y, z_calibracion):
        print(f"  X No alcanzable: ({coord.x:.1f}, {coord.y:.1f}, z={z_calibracion:+.1f}) cm")
        print("  Proba una casilla mas cercana o subi z_offset (menos negativo).")
        return

    try:
        angulos = sistema.calcular_angulos(coord.x, coord.y, z_calibracion)
        servos = sistema.angulos_a_servos(angulos)
    except Exception as e:
        print(f"  X Error calculando angulos: {e}")
        return

    # IMPORTANTE: volver a parked antes de cada movimiento para que el GOTO
    # arranque siempre desde la misma referencia. Sin esto, los movimientos
    # encadenados arrastran error de gear backlash / momentum.
    print("  Volviendo a HOME antes de moverse...")
    try:
        arduino.home()
    except Exception as e:
        print(f"  X Error mandando HOME: {e}")
        return

    print(f"  Coord robot: ({coord.x:.2f}, {coord.y:.2f}, z={z_calibracion:+.2f}) cm  [z_offset={z_offset:+.1f}]")
    print(f"  Angulos math: theta_rot={angulos.theta_rot:.1f} theta1={angulos.theta1:.1f} theta2={angulos.theta2:.1f}")
    print(f"  Servos: base={servos.base:.0f} brazo1={servos.brazo1:.0f} brazo2={servos.brazo2:.0f}")
    print("  Mandando GOTO al Arduino...")

    try:
        resp = arduino.enviar_goto(servos)
    except Exception as e:
        print(f"  X Error de comunicacion: {e}")
        return

    if not resp.startswith("OK"):
        print(f"  X Arduino respondio: {resp or '(timeout)'}")
        return

    print(f"  OK Brazo en posicion sobre {target}. Observa donde cayo la pinza.")
    actual = input(f"  ¿A que casilla llego? [Enter={target}, S=skip]: ").strip().upper()

    if actual == "S":
        print("  (Salteado, no se registra el par.)")
        # igual volvemos a home para dejar el brazo en posicion conocida
        arduino.home()
        return
    if not actual:
        actual = target

    try:
        actual_xyz = sistema.casilla_a_xyz(actual)
    except ValueError as e:
        print(f"  Casilla actual invalida ({e}). No se registra el par.")
        arduino.home()
        return

    pares.append((target, actual, coord, actual_xyz))
    dx = actual_xyz.x - coord.x
    dy = actual_xyz.y - coord.y
    print(f"  Registrado: {target} -> {actual}   Δx={dx:+.2f}  Δy={dy:+.2f} cm")

    # Mostrar visualmente target vs actual en el tablero.
    dibujar_tablero(target=target, actual=actual)

    # Volvemos a parked para que el proximo movimiento arranque limpio.
    arduino.home()


def listar_pares(pares):
    if not pares:
        print("  Sin pares registrados todavia.")
        return
    print()
    print("  Pares registrados:")
    print("  " + "-" * 56)
    print(f"  {'Target':>8}  {'Actual':>8}  {'Δx (cm)':>10}  {'Δy (cm)':>10}")
    print("  " + "-" * 56)
    for t, a, txy, axy in pares:
        dx = axy.x - txy.x
        dy = axy.y - txy.y
        print(f"  {t:>8}  {a:>8}  {dx:+10.2f}  {dy:+10.2f}")
    print("  " + "-" * 56)


def analizar(pares):
    if len(pares) < 2:
        print("  Necesitas al menos 2 pares. Usa 'm' para sumar mas.")
        return

    listar_pares(pares)

    deltas_x = [a.x - t.x for _, _, t, a in pares]
    deltas_y = [a.y - t.y for _, _, t, a in pares]
    avg_dx = sum(deltas_x) / len(deltas_x)
    avg_dy = sum(deltas_y) / len(deltas_y)
    var_dx = max(deltas_x) - min(deltas_x)
    var_dy = max(deltas_y) - min(deltas_y)

    print()
    print(f"  Promedio:  Δx={avg_dx:+.2f}  Δy={avg_dy:+.2f}  cm")
    print(f"  Variacion: rango_dx={var_dx:.2f}   rango_dy={var_dy:.2f}  cm")
    print()

    sugerir(avg_dx, avg_dy, var_dx, var_dy)


def sugerir(avg_dx, avg_dy, var_dx, var_dy):
    """
    Heuristicas simples para sugerir cambios de config.
    Convencion del proyecto: "actual" = celda donde fisicamente llego el brazo.
    Si actual_xy tiene mas Y que target, el brazo SE PASO de largo (fue mas lejos),
    asi que tenemos que reducir la coord Y que mandamos -> reducir OFFSET_BRAZO.
    """
    sugerencias = []

    # Δy sistematico chico → OFFSET_BRAZO mal calibrado.
    if abs(avg_dy) > 0.5 and var_dy < 1.5:
        nuevo = OFFSET_BRAZO - avg_dy
        sugerencias.append(
            f"OFFSET_BRAZO: actual={OFFSET_BRAZO} -> proba {nuevo:.1f}\n"
            f"     Razon: el brazo se desfasa Δy={avg_dy:+.2f} cm en Y de forma sistematica.\n"
            f"     Si Δy>0 (cayo mas LEJOS de lo pedido), reducir OFFSET_BRAZO.\n"
            f"     Si Δy<0 (cayo mas CERCA), aumentarlo."
        )

    # Δx sistematico chico → SERVO_BASE_OFFSET o desfasaje rotacional.
    if abs(avg_dx) > 0.5 and var_dx < 1.5:
        # Estimacion: a una Y promedio en el tablero, ¿cuanto tendria que rotar
        # la base para corregir avg_dx cm en X?
        y_centro_tablero = OFFSET_BRAZO + 8.0
        delta_grados = math.degrees(math.atan2(avg_dx, y_centro_tablero))
        nuevo = SERVO_BASE_OFFSET - delta_grados
        sugerencias.append(
            f"SERVO_BASE_OFFSET: actual={SERVO_BASE_OFFSET} -> proba {nuevo:.1f}\n"
            f"     Razon: el brazo cae con desfasaje X promedio de {avg_dx:+.2f} cm,\n"
            f"     ~equivalente a una rotacion de la base de {delta_grados:+.1f} grados.\n"
            f"     Si el brazo siempre cae a la DERECHA, restar mas.\n"
            f"     Si siempre cae a la IZQUIERDA, sumar."
        )

    # Variacion alta → escala mal o brazos de longitud equivocada.
    if var_dx > 1.5 or var_dy > 1.5:
        sugerencias.append(
            f"DIAMETRO_CASILLA: actual={DIAMETRO_CASILLA}\n"
            f"     La VARIACION de los deltas es alta (rango_dx={var_dx:.2f}, rango_dy={var_dy:.2f}).\n"
            f"     Eso indica que el espaciado entre celdas en config no coincide con el real,\n"
            f"     o que las longitudes LARGO_PRIMER_BRAZO / LARGO_SEGUNDO_BRAZO estan mal.\n"
            f"     Pasos sugeridos:\n"
            f"      a) Medi con regla 4 casillas reales: ¿que ancho dan? Dividi por 4 -> nuevo DIAMETRO_CASILLA.\n"
            f"      b) Volve a medir L1 (eje hombro -> eje muneca) y L2 (eje muneca -> punta pinza).\n"
            f"      c) Volve a correr el calibrador despues de ajustar."
        )

    if not sugerencias:
        print("  Los deltas son chicos. La calibracion parece OK.")
        print("  Pasa a probar python main.py con una jugada real.")
        return

    print("  +-- SUGERENCIAS --------------------------------------------+")
    for i, s in enumerate(sugerencias, 1):
        print(f"  | {i}. {s}")
        print("  |")
    print("  +-----------------------------------------------------------+")
    print("  Editar brazo_robotico/config.py, aplicar UN cambio por vez,")
    print("  volver a correr este calibrador y comparar deltas.")


if __name__ == "__main__":
    main()
