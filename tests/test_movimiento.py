from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.movimiento import Movimiento

def test_generar_secuencia():
    sistema = SistemaBrazo()
    mov = Movimiento(sistema, "A1", "C3")
    secuencia = mov.generar_secuencia()

    assert "inicio" in secuencia
    assert "fin" in secuencia
    assert hasattr(secuencia["inicio"], "theta_rot")
    assert hasattr(secuencia["fin"], "theta_rot")
    assert secuencia["inicio"].theta_rot != secuencia["fin"].theta_rot