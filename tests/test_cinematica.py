# tests/test_cinematica.py
import pytest
from brazo_robotico.cinematica import CinematicaInversa

def test_es_alcanzable():
    cin = CinematicaInversa()
    # L1=18, L2=20
    assert cin.es_alcanzable(10, 10, 18, 20) == True
    assert cin.es_alcanzable(50, 50, 18, 20) == False

def test_calcular_angulos():
    cin = CinematicaInversa()
    angulos = cin.calcular_angulos(10, 10, 18, 20)
    assert isinstance(angulos[0], float)
    assert isinstance(angulos[1], float)