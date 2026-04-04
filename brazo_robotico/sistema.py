from brazo_robotico.cinematica import CinematicaInversa
from brazo_robotico.tablero import Tablero
from brazo_robotico.tipos import Coordenada, Angulos, AngulosServo
from brazo_robotico.config import (
    DIAMETRO_CASILLA,
    LARGO_PRIMER_BRAZO,
    LARGO_SEGUNDO_BRAZO,
    OFFSET_BRAZO,
    PREFERENCIA_CODO,
    SERVO_BASE_OFFSET,
    SERVO_BASE_SIGNO,
    SERVO_BRAZO1_OFFSET,
    SERVO_BRAZO1_SIGNO,
    SERVO_BRAZO2_OFFSET,
    SERVO_BRAZO2_SIGNO,
    SERVO_MIN,
    SERVO_MAX,
)

class SistemaBrazo:
    def __init__(self):
        self.tablero = Tablero(tamaño_casilla=DIAMETRO_CASILLA)
        self.cinematica = CinematicaInversa()
        self.L1 = LARGO_PRIMER_BRAZO
        self.L2 = LARGO_SEGUNDO_BRAZO
        self.offset = OFFSET_BRAZO
        self.preferencia_codo = PREFERENCIA_CODO

    def casilla_a_xy(self, casilla: str) -> Coordenada:
        return self.casilla_a_xyz(casilla)

    def casilla_a_xyz(self, casilla: str) -> Coordenada:
        """
        Convierte una casilla del tablero a coordenadas del robot.

        El eje X queda centrado en el tablero para que la rotación de la base
        distinga correctamente los lados izquierdo y derecho. El eje Y se mide
        desde la base hasta el centro de la casilla objetivo.
        """
        coord = self.tablero.casilla_a_xy(casilla)
        medio_tablero = self.tablero.ancho / 2
        medio_casilla = self.tablero.tamaño_casilla / 2

        x_robot = coord.x - medio_tablero + medio_casilla
        y_robot = coord.y + self.offset + medio_casilla
        return Coordenada(x_robot, y_robot, 0.0)

    def es_alcanzable(self, x: float, y: float, z: float = 0.0) -> bool:
        return self.cinematica.es_alcanzable(x, y, self.L1, self.L2, z)

    def calcular_angulos(self, x: float, y: float, z: float = 0.0) -> Angulos:
        return self.cinematica.calcular_angulos(x, y, self.L1, self.L2, z, self.preferencia_codo)

    def angulos_a_servos(self, angulos: Angulos) -> AngulosServo:
        return AngulosServo(
            base=self._convertir_a_servo(angulos.theta_rot, SERVO_BASE_OFFSET, SERVO_BASE_SIGNO),
            brazo1=self._convertir_a_servo(angulos.theta1, SERVO_BRAZO1_OFFSET, SERVO_BRAZO1_SIGNO),
            brazo2=self._convertir_a_servo(abs(angulos.theta2), SERVO_BRAZO2_OFFSET, SERVO_BRAZO2_SIGNO),
        )

    def _convertir_a_servo(self, angulo: float, offset: float, signo: float) -> float:
        angulo_servo = offset + (signo * angulo)
        return max(SERVO_MIN, min(SERVO_MAX, angulo_servo))