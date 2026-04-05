import time
from rich.console import Console
from rich.table import Table
from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.movimiento import Movimiento
from brazo_robotico.visualizacion import mostrar_visualizacion_2d, mostrar_visualizacion_3d

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
    ang_inicio = secuencia["inicio"]
    ang_fin = secuencia["fin"]

    table = Table(title="Movimiento del Brazo Robótico")
    table.add_column("Paso", justify="center")
    table.add_column("Rotación Base (°)", justify="center")
    table.add_column("Inclinación Brazo 1 (°)", justify="center")
    table.add_column("Inclinación Brazo 2 (°)", justify="center")
    table.add_row("Inicio", f"{ang_inicio.theta_rot:.2f}", f"{ang_inicio.theta1:.2f}", f"{ang_inicio.theta2:.2f}")
    table.add_row("Final", f"{ang_fin.theta_rot:.2f}", f"{ang_fin.theta1:.2f}", f"{ang_fin.theta2:.2f}")
    console.print(table)
    time.sleep(1)

    servos_inicio = sistema.angulos_a_servos(ang_inicio)
    servos_fin = sistema.angulos_a_servos(ang_fin)

    table_servos = Table(title="Ángulos para Servos")
    table_servos.add_column("Paso", justify="center")
    table_servos.add_column("Servo Base (°)", justify="center")
    table_servos.add_column("Servo Brazo 1 (°)", justify="center")
    table_servos.add_column("Servo Brazo 2 (°)", justify="center")
    table_servos.add_row("Inicio", f"{servos_inicio.base:.2f}", f"{servos_inicio.brazo1:.2f}", f"{servos_inicio.brazo2:.2f}")
    table_servos.add_row("Final", f"{servos_fin.base:.2f}", f"{servos_fin.brazo1:.2f}", f"{servos_fin.brazo2:.2f}")
    console.print(table_servos)
    time.sleep(1)

    modo_vista = console.input("¿Visualización [bold](2D/3D/n)[/bold]? (Enter=2D): ").strip().lower()
    if modo_vista not in ("n", "no"):
        try:
            if modo_vista in ("3", "3d"):
                vista_brazo = console.input("¿Mostrar brazo? [bold](inicio/final/ambos)[/bold] (Enter=ambos): ").strip().lower()
                if vista_brazo in ("i", "inicio"):
                    vista = "inicio"
                elif vista_brazo in ("f", "final"):
                    vista = "final"
                else:
                    vista = "ambos"
                mostrar_visualizacion_3d(sistema, casilla_inicio, casilla_fin, secuencia, vista=vista)
            else:
                mostrar_visualizacion_2d(sistema, casilla_inicio, casilla_fin, secuencia)
        except ModuleNotFoundError as error:
            if error.name == "matplotlib":
                console.print(
                    "[red]No se encontró matplotlib en este entorno.[/red]\n"
                    "Instala dependencias con: [bold]pip install -r requirements.txt[/bold]"
                )
            else:
                raise

    console.print("[bold blue]Movimiento completado![/bold blue]")

if __name__ == "__main__":
    main()