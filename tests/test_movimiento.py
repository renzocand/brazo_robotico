# tests/test_movimiento.py
import pytest
from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.movimiento import Movimiento

def test_generar_secuencia():
    sistema = SistemaBrazo()
    mov = Movimiento(sistema, "A1", "C3")
    secuencia = mov.generar_secuencia()

    assert "inicio" in secuencia
    assert "fin" in secuencia
    assert len(secuencia["inicio"]) == 2
    assert len(secuencia["fin"]) == 2