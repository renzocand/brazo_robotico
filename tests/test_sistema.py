from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.config import DIAMETRO_CASILLA, OFFSET_BRAZO

def test_facade():
    sistema = SistemaBrazo()
    coord = sistema.casilla_a_xy("B2")
    assert coord.x == -7.5
    assert coord.y == OFFSET_BRAZO + DIAMETRO_CASILLA + (DIAMETRO_CASILLA / 2)
    assert coord.z == 0.0