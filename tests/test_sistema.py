from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.config import DIAMETRO_CASILLA, OFFSET_BRAZO

def test_facade():
    sistema = SistemaBrazo()
    coord = sistema.casilla_a_xy("B2")
    # B2: columna 1, fila 1 -> centrado respecto al tablero
    medio_tablero = 8 * DIAMETRO_CASILLA / 2
    medio_casilla = DIAMETRO_CASILLA / 2
    assert coord.x == (1 * DIAMETRO_CASILLA) - medio_tablero + medio_casilla
    assert coord.y == OFFSET_BRAZO + DIAMETRO_CASILLA + medio_casilla
    assert coord.z == 0.0