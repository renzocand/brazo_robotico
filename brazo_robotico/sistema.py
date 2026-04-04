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
        self.offset = OFFSET_BRAZO  # distancia vertical del brazo al tablero

    # Wrapper para convertir casilla de ajedrez a coordenadas XY
    def casilla_a_xy(self, casilla: str) -> Coordenada:
        coord = self.tablero.casilla_a_xy(casilla)
        # sumamos el offset físico para el cálculo real del brazo
        return Coordenada(coord.x, coord.y + self.offset)

    # Wrapper para verificar si la posición es alcanzable
    def es_alcanzable(self, x: float, y: float) -> bool:
        return self.cinematica.es_alcanzable(x, y, self.L1, self.L2)

    # Wrapper para calcular los ángulos (ahora 3)
    def calcular_angulos(self, x: float, y: float) -> Angulos:
        return self.cinematica.calcular_angulos(x, y + self.offset, self.L1, self.L2)