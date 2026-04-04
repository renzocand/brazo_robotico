from math import sqrt, atan2, acos, cos, sin, degrees, pi
from brazo_robotico.tipos import Angulos

class CinematicaInversa:
    def es_alcanzable(self, x: float, y: float, L1: float, L2: float) -> bool:
        """
        Devuelve True si el punto (x,y) está dentro del alcance del brazo.
        """
        distancia = sqrt(x**2 + y**2)
        return distancia <= (L1 + L2) and distancia >= abs(L1 - L2)

    def calcular_angulos(self, x: float, y: float, L1: float, L2: float) -> Angulos:
        """
        Calcula los 3 ángulos:
        - theta_rot: rotación de la base en plano XY
        - theta1: inclinación del primer brazo
        - theta2: inclinación del segundo brazo
        """
        # 1. Rotación de la base
        theta_rot = degrees(atan2(y, x))
        r = sqrt(x**2 + y**2)  # distancia radial en el plano XY

        if not self.es_alcanzable(r, 0, L1, L2):
            raise ValueError(f"Posición ({x},{y}) fuera de alcance")

        # Ley de cosenos para segundo brazo
        cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
        cos_theta2 = max(min(cos_theta2, 1.0), -1.0)  # evitar errores numéricos
        theta2 = degrees(acos(cos_theta2))

        # Ángulo del primer brazo
        k1 = L1 + L2 * cos(theta2 * pi / 180)
        k2 = L2 * sin(theta2 * pi / 180)
        theta1 = degrees(atan2(0, r) - atan2(k2, k1))

        return Angulos(theta_rot, theta1, theta2)