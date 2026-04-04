# tests/test_tablero.py
import pytest
from brazo_robotico.tablero import Tablero

def test_casilla_a_xy():
    tablero = Tablero(tamaño_casilla=3.0)
    # 'A1' debe ser (0,0)
    coord = tablero.casilla_a_xy("A1")
    assert coord.x == 0
    assert coord.y == 0

    # 'C4' -> x=6, y=9
    coord = tablero.casilla_a_xy("C4")
    assert coord.x == 6
    assert coord.y == 9