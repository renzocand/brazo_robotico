# tests/test_cinematica.py
from brazo_robotico.cinematica import CinematicaInversa

def test_es_alcanzable():
    cin = CinematicaInversa()
    # L1=18, L2=20
    assert cin.es_alcanzable(10, 10, 18, 20) == True
    assert cin.es_alcanzable(50, 50, 18, 20) == False

def test_calcular_angulos():
    cin = CinematicaInversa()
    angulos = cin.calcular_angulos(10, 10, 18, 20)
    assert isinstance(angulos.theta_rot, float)
    assert isinstance(angulos.theta1, float)
    assert isinstance(angulos.theta2, float)

def test_rotacion_base_cambia_con_lado_del_tablero():
    cin = CinematicaInversa()
    izquierda = cin.calcular_angulos(-9, 16, 18, 20)
    derecha = cin.calcular_angulos(9, 16, 18, 20)

    assert izquierda.theta_rot > 90.0
    assert derecha.theta_rot < 90.0