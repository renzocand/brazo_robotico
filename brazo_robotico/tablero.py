# brazo_robotico/tablero.py
from .tipos import Coordenada
from .config import INVERTIR_FILAS_TABLERO

class Tablero:
    def __init__(self, filas: int = 8, columnas: int = 8, tamaño_casilla: float = 3.0):
        self.filas = filas
        self.columnas = columnas
        self.tamaño_casilla = tamaño_casilla

    @property
    def ancho(self) -> float:
        return self.columnas * self.tamaño_casilla

    @property
    def alto(self) -> float:
        return self.filas * self.tamaño_casilla

    def casilla_a_xy(self, casilla: str) -> Coordenada:
        """
        Convierte una casilla tipo 'A6' a coordenadas (x, y) en cm.
        Ejemplo (sin invertir): 'A1' -> (0,0), 'C4' -> (6, 9)

        Si INVERTIR_FILAS_TABLERO=True, la fila 8 queda CERCA del brazo
        (y=0) y la fila 1 LEJOS (y máx). Esto se usa cuando el tablero
        físico está orientado al revés respecto a la convención del código.
        """
        if len(casilla) != 2:
            raise ValueError(f"Casilla inválida: {casilla}")

        columna = ord(casilla[0].upper()) - ord('A')
        fila = int(casilla[1]) - 1

        if not (0 <= columna < self.columnas) or not (0 <= fila < self.filas):
            raise ValueError(f"Casilla inválida: {casilla}")

        x = columna * self.tamaño_casilla
        if INVERTIR_FILAS_TABLERO:
            y = (self.filas - 1 - fila) * self.tamaño_casilla
        else:
            y = fila * self.tamaño_casilla
        return Coordenada(x, y)