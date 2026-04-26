from dataclasses import dataclass

@dataclass
class Coordenada:
    x: float
    y: float
    z: float = 0.0

@dataclass
class Angulos:
    theta_rot: float  # rotación base
    theta1: float     # primer brazo
    theta2: float     # segundo brazo

@dataclass
class AngulosServo:
    base: float       # servo 1 — rotación de la base
    brazo1: float     # servo 2 — codo
    brazo2: float     # servo 3 — muñeca
    pinza: float = 0.0  # servo 4 — 0 = abre, 60 = cierra