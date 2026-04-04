from math import sqrt, atan2, acos, cos, sin, degrees, radians
from brazo_robotico.tipos import Angulos

class CinematicaInversa:
    def es_alcanzable(self, x: float, y: float, L1: float, L2: float, z: float = 0.0) -> bool:
        """
        Devuelve True si el punto (x,y,z) está dentro del alcance del brazo.

        x: desplazamiento lateral, y: distancia frontal, z: altura.
        """
        distancia_horizontal = sqrt(x**2 + y**2)
        distancia = sqrt((distancia_horizontal**2) + (z**2))
        return distancia <= (L1 + L2) and distancia >= abs(L1 - L2)

    def calcular_angulos(self, x: float, y: float, L1: float, L2: float, z: float = 0.0) -> Angulos:
        """
        Calcula los 3 ángulos del brazo.

        x: desplazamiento lateral respecto al centro del robot.
        y: distancia frontal desde la base hacia el tablero.
        z: altura respecto al plano del tablero.

        La base gira en XY y el hombro/codo se resuelven en el plano r-z.
        """
        theta_rot = 90.0 - degrees(atan2(x, y))
        distancia_radial = sqrt(x**2 + y**2)
        distancia_objetivo = sqrt((distancia_radial**2) + (z**2))

        if not self.es_alcanzable(x, y, L1, L2, z):
            raise ValueError(f"Posición ({x},{y},{z}) fuera de alcance")

        cos_theta2 = (distancia_objetivo**2 - L1**2 - L2**2) / (2 * L1 * L2)
        cos_theta2 = max(min(cos_theta2, 1.0), -1.0)
        theta2 = degrees(acos(cos_theta2))

        theta2_rad = radians(theta2)
        k1 = L1 + L2 * cos(theta2_rad)
        k2 = L2 * sin(theta2_rad)
        theta1 = degrees(atan2(z, distancia_radial) - atan2(k2, k1))

        return Angulos(theta_rot, theta1, theta2)