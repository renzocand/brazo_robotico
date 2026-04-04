import time
from rich.console import Console
from rich.table import Table
from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.movimiento import Movimiento

console = Console()

def main():
    console.print("[bold green]=== Brazo Robótico Ajedrez ===[/bold green]")

    sistema = SistemaBrazo()

    # Pedir al usuario las casillas
    casilla_inicio = console.input("Ingresa casilla inicial (ej. A2): ").strip().upper()
    casilla_fin = console.input("Ingresa casilla final (ej. C4): ").strip().upper()

    mov = Movimiento(sistema, casilla_inicio, casilla_fin)
    try:
        secuencia = mov.generar_secuencia()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        return

    # Mostrar secuencia paso a paso
    table = Table(title="Movimiento del Brazo Robótico")
    table.add_column("Paso", justify="center")
    table.add_column("Rotación Base (°)", justify="center")
    table.add_column("Inclinación Brazo 1 (°)", justify="center")
    table.add_column("Inclinación Brazo 2 (°)", justify="center")

    # Paso 1: ir a posición inicial
    ang_inicio = secuencia["inicio"]
    table.add_row("Inicio", f"{ang_inicio.theta_rot:.2f}", f"{ang_inicio.theta1:.2f}", f"{ang_inicio.theta2:.2f}")
    console.print(table)
    time.sleep(1)

    # Paso 2: ir a posición final
    ang_fin = secuencia["fin"]
    table.add_row("Final", f"{ang_fin.theta_rot:.2f}", f"{ang_fin.theta1:.2f}", f"{ang_fin.theta2:.2f}")
    console.print(table)
    time.sleep(1)

    console.print("[bold blue]Movimiento completado![/bold blue]")

if __name__ == "__main__":
    main()