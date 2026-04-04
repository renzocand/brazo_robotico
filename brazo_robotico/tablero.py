# brazo_robotico/tablero.py
from .tipos import Coordenada

class Tablero:
    def __init__(self, filas: int = 8, columnas: int = 8, tamaño_casilla: float = 3.0):
        self.filas = filas
        self.columnas = columnas
        self.tamaño_casilla = tamaño_casilla

    def casilla_a_xy(self, casilla: str) -> Coordenada:
        """
        Convierte una casilla tipo 'A6' a coordenadas (x, y) en cm.
        Ejemplo: 'A1' -> (0,0), 'C4' -> (6, 9)
        """
        columna = ord(casilla[0].upper()) - ord('A')
        fila = int(casilla[1]) - 1
        x = columna * self.tamaño_casilla
        y = fila * self.tamaño_casilla
        return Coordenada(x, y)