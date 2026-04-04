from brazo_robotico.cinematica import CinematicaInversa
from brazo_robotico.tablero import Tablero
from brazo_robotico.tipos import Coordenada, Angulos
from brazo_robotico.config import DIAMETRO_CASILLA, LARGO_PRIMER_BRAZO, LARGO_SEGUNDO_BRAZO, OFFSET_BRAZO

class SistemaBrazo:
    def __init__(self):
        self.tablero = Tablero(tamaño_casilla=DIAMETRO_CASILLA)
        self.cinematica = CinematicaInversa()
        self.L1 = LARGO_PRIMER_BRAZO
        self.L2 = LARGO_SEGUNDO_BRAZO
        self.offset = OFFSET_BRAZO

    def casilla_a_xy(self, casilla: str) -> Coordenada:
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
        return Coordenada(x_robot, y_robot)

    def es_alcanzable(self, x: float, y: float) -> bool:
        return self.cinematica.es_alcanzable(x, y, self.L1, self.L2)

    def calcular_angulos(self, x: float, y: float) -> Angulos:
        return self.cinematica.calcular_angulos(x, y, self.L1, self.L2)