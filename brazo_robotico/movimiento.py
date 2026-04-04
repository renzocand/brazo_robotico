from .sistema import SistemaBrazo
from .tipos import Angulos

class Movimiento:
    def __init__(self, sistema: SistemaBrazo, casilla_inicio: str, casilla_fin: str):
        self.sistema = sistema
        self.casilla_inicio = casilla_inicio
        self.casilla_fin = casilla_fin

    def generar_secuencia(self) -> dict[str, Angulos]:
        """
        Devuelve la secuencia de ángulos para mover la pieza:
        "inicio" -> casilla inicial
        "fin" -> casilla final
        """
        inicio = self.sistema.casilla_a_xy(self.casilla_inicio)
        fin = self.sistema.casilla_a_xy(self.casilla_fin)

        # Validación
        if not self.sistema.es_alcanzable(inicio.x, inicio.y, inicio.z):
            raise ValueError(f"Posición inicial {self.casilla_inicio} no alcanzable")
        if not self.sistema.es_alcanzable(fin.x, fin.y, fin.z):
            raise ValueError(f"Posición final {self.casilla_fin} no alcanzable")

        # Cálculo de ángulos (ahora 3)
        angulos_inicio = self.sistema.calcular_angulos(inicio.x, inicio.y, inicio.z)
        angulos_fin = self.sistema.calcular_angulos(fin.x, fin.y, fin.z)

        return {
            "inicio": angulos_inicio,
            "fin": angulos_fin
        }