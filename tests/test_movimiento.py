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

def test_conversion_a_servos():
    sistema = SistemaBrazo()
    mov = Movimiento(sistema, "A3", "F4")
    secuencia = mov.generar_secuencia()

    servos_inicio = sistema.angulos_a_servos(secuencia["inicio"])
    servos_fin = sistema.angulos_a_servos(secuencia["fin"])

    assert 0.0 <= servos_inicio.base <= 180.0
    assert 0.0 <= servos_inicio.brazo1 <= 180.0
    assert 0.0 <= servos_inicio.brazo2 <= 180.0
    assert 0.0 <= servos_fin.base <= 180.0
    assert 0.0 <= servos_fin.brazo1 <= 180.0
    assert 0.0 <= servos_fin.brazo2 <= 180.0