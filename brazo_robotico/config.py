# brazo_robotico/config.py

# Tamaño de los cuadrados del tablero
DIAMETRO_CASILLA = 2.5  # cm — tablero total de 20x20 cm

# Longitudes reales del brazo (medidas con regla)
LARGO_PRIMER_BRAZO = 15.0   # L1: del eje del hombro al eje de la muñeca, cm
LARGO_SEGUNDO_BRAZO = 15.9  # L2: del eje de la muñeca a la punta de la pinza, cm

# Distancia del brazo al borde más cercano del tablero
OFFSET_BRAZO = 5.0  # cm

# Rama preferida de la cinemática inversa.
# "arriba": el codo queda por encima del tablero.
# "abajo": solución espejo.
PREFERENCIA_CODO = "arriba"

# Conversión de ángulos matemáticos a servos.
# Ajusta estos offsets y sentidos según el montaje real del brazo.
# Los límites por servo deben coincidir con los del sketch Arduino.
SERVO_MIN = 0.0
SERVO_MAX = 180.0

# Margen de 10° en cada extremo para evitar que los servos se queden
# forzando contra topes mecánicos (causa común de quemado de servos).
SERVO_BASE_MIN = 10.0
SERVO_BASE_MAX = 170.0
SERVO_BASE_OFFSET = 0.0     # math theta_rot=0 → servo 0 (un extremo); 180 → servo 180 (otro extremo)
SERVO_BASE_SIGNO = 1.0

SERVO_BRAZO1_MIN = 10.0
SERVO_BRAZO1_MAX = 170.0
SERVO_BRAZO1_OFFSET = 90.0  # math theta1=0 (horizontal) → servo 90 (centrado)
SERVO_BRAZO1_SIGNO = 1.0

SERVO_BRAZO2_MIN = 10.0
SERVO_BRAZO2_MAX = 170.0
SERVO_BRAZO2_OFFSET = 0.0   # math abs(theta2)=0 → servo 0; abs=180 → servo 180
SERVO_BRAZO2_SIGNO = 1.0

# Pinza — solo dos posiciones (no requiere conversión)
PINZA_ABIERTA = 0.0    # ° pinza abierta
PINZA_CERRADA = 60.0   # ° pinza cerrada

# ──────────────────────────────────────────────
# CONEXIÓN ARDUINO
# ──────────────────────────────────────────────

# Puerto serie del Arduino. None = autodetectar.
# Ejemplos:
#   Windows: "COM3"
#   Linux:   "/dev/ttyACM0"
#   macOS:   "/dev/cu.usbmodem14101"
ARDUINO_PUERTO = "COM4"

# Baudios — debe coincidir con `BAUDIOS` en el sketch del Arduino
ARDUINO_BAUDIOS = 9600

# Si True, el juego intenta conectarse al Arduino al iniciar.
# Si False, el juego solo muestra los ángulos por pantalla (modo simulación).
ARDUINO_HABILITADO = True

# Estos valores DEBEN coincidir con los del sketch para que la animación
# en pantalla se sincronice con el movimiento real del brazo.
ARDUINO_MS_POR_PASO = 120        # = MS_POR_PASO en el .ino
ARDUINO_PAUSA_AGARRE_MS = 2000   # = PAUSA_AGARRE en el .ino
ARDUINO_PARKED_BASE = 90        # = PARKED_BASE en el .ino
ARDUINO_PARKED_BRAZO1 = 90      # = PARKED_BRAZO1 en el .ino
ARDUINO_PARKED_BRAZO2 = 90      # = PARKED_BRAZO2 en el .ino