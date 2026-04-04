import pytest
from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.config import DIAMETRO_CASILLA, OFFSET_BRAZO

def test_facade():
    sistema = SistemaBrazo()
    coord = sistema.casilla_a_xy("B2")
    assert coord.x == DIAMETRO_CASILLA
    assert coord.y == DIAMETRO_CASILLA + OFFSET_BRAZO