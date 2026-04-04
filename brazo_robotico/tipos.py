from dataclasses import dataclass

@dataclass
class Coordenada:
    x: float
    y: float

@dataclass
class Angulos:
    theta_rot: float  # rotación base
    theta1: float     # primer brazo
    theta2: float     # segundo brazo