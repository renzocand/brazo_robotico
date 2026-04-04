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
    base: float
    brazo1: float
    brazo2: float