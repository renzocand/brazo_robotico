# brazo_robotico/config.py

# Tamaño de los cuadrados del tablero
DIAMETRO_CASILLA = 3.0  # cm

# Longitudes de los brazos
LARGO_PRIMER_BRAZO = 23.0  # cm
LARGO_SEGUNDO_BRAZO = 19.0  # cm

# Distancia del brazo al tablero
OFFSET_BRAZO = 10.0  # cm

# Rama preferida de la cinemática inversa.
# "arriba": el codo queda por encima del tablero.
# "abajo": solución espejo.
PREFERENCIA_CODO = "arriba"

# Conversión de ángulos matemáticos a servos.
# Ajusta estos offsets y sentidos según el montaje real del brazo.
SERVO_MIN = 0.0
SERVO_MAX = 180.0

SERVO_BASE_OFFSET = 0.0
SERVO_BASE_SIGNO = 1.0

SERVO_BRAZO1_OFFSET = 90.0
SERVO_BRAZO1_SIGNO = 1.0

SERVO_BRAZO2_OFFSET = 0.0
SERVO_BRAZO2_SIGNO = 1.0