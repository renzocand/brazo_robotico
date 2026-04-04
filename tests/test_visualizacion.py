from brazo_robotico.tipos import Angulos
from brazo_robotico.visualizacion import calcular_articulaciones


def test_calcular_articulaciones_alcanza_objetivo_radial():
    angulos = Angulos(theta_rot=90.0, theta1=-30.0, theta2=60.0)
    codo, efector = calcular_articulaciones(angulos, 10.0, 10.0)

    assert codo.x > 0.0
    assert efector.x > codo.x
    assert round(efector.z, 6) == 0.0