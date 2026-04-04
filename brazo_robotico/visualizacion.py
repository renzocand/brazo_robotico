from math import cos, radians, sin

from brazo_robotico.tipos import Angulos, Coordenada


def calcular_articulaciones(angulos: Angulos, L1: float, L2: float) -> tuple[Coordenada, Coordenada]:
    theta1_rad = radians(angulos.theta1)
    theta12_rad = radians(angulos.theta1 + angulos.theta2)

    codo = Coordenada(
        x=L1 * cos(theta1_rad),
        y=0.0,
        z=L1 * sin(theta1_rad),
    )
    efector = Coordenada(
        x=codo.x + (L2 * cos(theta12_rad)),
        y=0.0,
        z=codo.z + (L2 * sin(theta12_rad)),
    )
    return codo, efector


def crear_visualizacion(sistema, casilla_inicio: str, casilla_fin: str, secuencia: dict[str, Angulos]):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Arc, Rectangle

    coord_inicio = sistema.casilla_a_xy(casilla_inicio)
    coord_fin = sistema.casilla_a_xy(casilla_fin)
    ang_inicio = secuencia["inicio"]
    ang_fin = secuencia["fin"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Visualización 2D del Brazo Robótico", fontsize=16)

    _dibujar_tablero(axes[0], sistema, casilla_inicio, casilla_fin, coord_inicio, coord_fin, ang_inicio, ang_fin, Arc, Rectangle)
    _dibujar_plano_brazo(axes[1], sistema, casilla_inicio, ang_inicio, "Inicio", "#0b7285", Arc)
    _dibujar_plano_brazo(axes[2], sistema, casilla_fin, ang_fin, "Final", "#c92a2a", Arc)

    fig.tight_layout()
    return fig


def mostrar_visualizacion(sistema, casilla_inicio: str, casilla_fin: str, secuencia: dict[str, Angulos]) -> None:
    mostrar_visualizacion_2d(sistema, casilla_inicio, casilla_fin, secuencia)


def mostrar_visualizacion_2d(sistema, casilla_inicio: str, casilla_fin: str, secuencia: dict[str, Angulos]) -> None:
    import matplotlib.pyplot as plt

    fig = crear_visualizacion(sistema, casilla_inicio, casilla_fin, secuencia)
    plt.show()
    plt.close(fig)


def mostrar_visualizacion_3d(sistema, casilla_inicio: str, casilla_fin: str, secuencia: dict[str, Angulos]) -> None:
    import matplotlib.pyplot as plt

    coord_inicio = sistema.casilla_a_xy(casilla_inicio)
    coord_fin = sistema.casilla_a_xy(casilla_fin)
    ang_inicio = secuencia["inicio"]
    ang_fin = secuencia["fin"]
    servos_inicio = sistema.angulos_a_servos(ang_inicio)
    servos_fin = sistema.angulos_a_servos(ang_fin)

    fig = plt.figure(figsize=(13, 9))
    ax = fig.add_subplot(111, projection="3d")
    fig.suptitle("Visualización 3D del Brazo Robótico", fontsize=16)

    base_y = 0.0

    _dibujar_tablero_3d(ax, sistema, casilla_inicio, casilla_fin)

    brazo_inicio = _proyectar_brazo_3d(ang_inicio, sistema.L1, sistema.L2, base_y=base_y)
    brazo_fin = _proyectar_brazo_3d(ang_fin, sistema.L1, sistema.L2, base_y=base_y)

    _dibujar_brazo_3d(ax, brazo_inicio, "#0b7285", f"Inicio {casilla_inicio}")
    _dibujar_brazo_3d(ax, brazo_fin, "#c92a2a", f"Final {casilla_fin}")

    ax.scatter(0, base_y, 0, color="#212529", s=45)
    ax.text(0.6, base_y + 0.4, 0.2, "Base", color="#212529")
    ax.plot([0, 0], [0, sistema.offset], [0, 0], linestyle="--", color="#868e96", linewidth=1.2)

    altura_indicador = 1.2
    ax.plot([coord_inicio.x, coord_inicio.x], [coord_inicio.y, coord_inicio.y], [0, altura_indicador], linestyle="--", color="#0b7285", linewidth=1.2)
    ax.plot([coord_fin.x, coord_fin.x], [coord_fin.y, coord_fin.y], [0, altura_indicador], linestyle="--", color="#c92a2a", linewidth=1.2)
    ax.scatter(coord_inicio.x, coord_inicio.y, altura_indicador, color="#0b7285", s=72, depthshade=False)
    ax.scatter(coord_fin.x, coord_fin.y, altura_indicador, color="#c92a2a", s=72, depthshade=False)
    ax.text(coord_inicio.x, coord_inicio.y, altura_indicador + 0.45, f"{casilla_inicio}", color="#0b7285", fontsize=10, weight="bold")
    ax.text(coord_fin.x, coord_fin.y, altura_indicador + 0.45, f"{casilla_fin}", color="#c92a2a", fontsize=10, weight="bold")

    resumen = (
        f"Inicio  Base={servos_inicio.base:.1f}°, S1={servos_inicio.brazo1:.1f}°, S2={servos_inicio.brazo2:.1f}°\n"
        f"Final   Base={servos_fin.base:.1f}°, S1={servos_fin.brazo1:.1f}°, S2={servos_fin.brazo2:.1f}°"
    )
    ax.text2D(
        0.03,
        0.95,
        resumen,
        transform=ax.transAxes,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )

    puntos = [
        (0.0, base_y, 0.0),
        (coord_inicio.x, coord_inicio.y, 0.0),
        (coord_fin.x, coord_fin.y, 0.0),
        *brazo_inicio,
        *brazo_fin,
    ]
    _ajustar_limites_3d(ax, puntos)

    ax.set_xlabel("X lateral (cm)")
    ax.set_ylabel("Y frontal (cm)")
    ax.set_zlabel("Z (cm)")
    ax.set_box_aspect((1.35, 1.55, 0.75))
    ax.view_init(elev=31, azim=-52)
    ax.grid(alpha=0.25)

    # Fondo más limpio para mejorar legibilidad.
    ax.xaxis.pane.set_alpha(0.05)
    ax.yaxis.pane.set_alpha(0.05)
    ax.zaxis.pane.set_alpha(0.05)
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.show()
    plt.close(fig)


def _dibujar_tablero(ax, sistema, casilla_inicio: str, casilla_fin: str, coord_inicio: Coordenada, coord_fin: Coordenada, ang_inicio: Angulos, ang_fin: Angulos, Arc, Rectangle) -> None:
    tamaño = sistema.tablero.tamaño_casilla
    origen_x = -sistema.tablero.ancho / 2
    origen_y = sistema.offset

    colores = ("#f2e9dc", "#9c6644")
    for fila in range(sistema.tablero.filas):
        for columna in range(sistema.tablero.columnas):
            color = colores[(fila + columna) % 2]
            ax.add_patch(
                Rectangle(
                    (origen_x + (columna * tamaño), origen_y + (fila * tamaño)),
                    tamaño,
                    tamaño,
                    facecolor=color,
                    edgecolor="#3d2b1f",
                    linewidth=0.5,
                )
            )

    ax.scatter(0, 0, color="#212529", s=60, label="Base")
    ax.scatter(coord_inicio.x, coord_inicio.y, color="#0b7285", s=70, label=f"Inicio {casilla_inicio}")
    ax.scatter(coord_fin.x, coord_fin.y, color="#c92a2a", s=70, label=f"Final {casilla_fin}")

    ax.plot([0, coord_inicio.x], [0, coord_inicio.y], linestyle="--", color="#0b7285", linewidth=1.5)
    ax.plot([0, coord_fin.x], [0, coord_fin.y], linestyle="--", color="#c92a2a", linewidth=1.5)

    radio_arco = 5
    ax.add_patch(Arc((0, 0), radio_arco, radio_arco, theta1=0, theta2=ang_inicio.theta_rot, color="#0b7285", linewidth=2))
    ax.add_patch(Arc((0, 0), radio_arco + 2, radio_arco + 2, theta1=0, theta2=ang_fin.theta_rot, color="#c92a2a", linewidth=2))

    ax.text(coord_inicio.x + 0.4, coord_inicio.y + 0.4, f"{casilla_inicio}\n{ang_inicio.theta_rot:.1f}°", color="#0b7285")
    ax.text(coord_fin.x + 0.4, coord_fin.y + 0.4, f"{casilla_fin}\n{ang_fin.theta_rot:.1f}°", color="#c92a2a")

    for indice, letra in enumerate("ABCDEFGH"):
        ax.text(origen_x + (indice * tamaño) + (tamaño / 2), origen_y - 1.2, letra, ha="center", va="center")
    for indice in range(8):
        ax.text(origen_x - 1.0, origen_y + (indice * tamaño) + (tamaño / 2), str(indice + 1), ha="center", va="center")

    ax.set_title("Vista superior del tablero")
    ax.set_xlabel("Eje X del robot (cm)")
    ax.set_ylabel("Eje Y del robot (cm)")
    ax.set_aspect("equal")
    ax.set_xlim(origen_x - 4, origen_x + sistema.tablero.ancho + 4)
    ax.set_ylim(-4, origen_y + sistema.tablero.alto + 3)
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right")


def _dibujar_plano_brazo(ax, sistema, casilla: str, angulos: Angulos, etiqueta: str, color: str, Arc) -> None:
    codo, efector = calcular_articulaciones(angulos, sistema.L1, sistema.L2)
    radio_objetivo = (efector.x**2 + efector.y**2) ** 0.5
    servos = sistema.angulos_a_servos(angulos)

    ax.plot([0, codo.x], [0, codo.z], color=color, linewidth=4)
    ax.plot([codo.x, efector.x], [codo.z, efector.z], color="#495057", linewidth=4)
    ax.scatter([0, codo.x, efector.x], [0, codo.z, efector.z], color=["#212529", color, "#fab005"], s=50)
    ax.plot([0, radio_objetivo], [0, 0], linestyle=":", color="#868e96")

    radio_hombro = max(sistema.L1 * 0.35, 2.5)
    theta_hombro_inicio = min(0, angulos.theta1)
    theta_hombro_fin = max(0, angulos.theta1)
    ax.add_patch(Arc((0, 0), radio_hombro, radio_hombro, theta1=theta_hombro_inicio, theta2=theta_hombro_fin, color=color, linewidth=2))

    orientacion_segundo = angulos.theta1 + angulos.theta2
    theta_codo_inicio = min(angulos.theta1, orientacion_segundo)
    theta_codo_fin = max(angulos.theta1, orientacion_segundo)
    ax.add_patch(Arc((codo.x, codo.y), 4.5, 4.5, theta1=theta_codo_inicio, theta2=theta_codo_fin, color="#495057", linewidth=2))

    ax.text(0.8, 1.0, f"Servo 1 = {servos.brazo1:.1f}°", color=color)
    ax.text(codo.x + 0.8, codo.z + 0.8, f"Servo 2 = {servos.brazo2:.1f}°", color="#495057")
    ax.text(
        0.02,
        0.98,
        (
            f"{etiqueta} {casilla}\n"
            f"Base: {angulos.theta_rot:.1f}°\n"
            f"Brazo 1: {angulos.theta1:.1f}°\n"
            f"Brazo 2: {angulos.theta2:.1f}°\n"
            f"Servo base: {servos.base:.1f}°\n"
            f"Servo 1: {servos.brazo1:.1f}°\n"
            f"Servo 2: {servos.brazo2:.1f}°"
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )

    alcance = sistema.L1 + sistema.L2 + 2
    ax.set_title(f"Plano del brazo: {etiqueta}")
    ax.set_xlabel("Distancia radial (cm)")
    ax.set_ylabel("Altura del plano 2D (cm)")
    ax.set_xlim(-2, alcance)
    ax.set_ylim(-alcance / 2, alcance / 2)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)


def _proyectar_brazo_3d(angulos: Angulos, L1: float, L2: float, base_y: float = 0.0) -> list[tuple[float, float, float]]:
    codo, efector = calcular_articulaciones(angulos, L1, L2)
    theta_base = radians(angulos.theta_rot)

    codo_radio = codo.x
    efector_radio = efector.x

    codo_x = codo_radio * cos(theta_base)
    codo_y = base_y + (codo_radio * sin(theta_base))
    codo_z = max(0.0, codo.z)

    efector_x = efector_radio * cos(theta_base)
    efector_y = base_y + (efector_radio * sin(theta_base))
    efector_z = max(1.2, max(0.0, efector.z))

    return [(0.0, base_y, 0.0), (codo_x, codo_y, codo_z), (efector_x, efector_y, efector_z)]


def _dibujar_brazo_3d(ax, puntos: list[tuple[float, float, float]], color: str, etiqueta: str) -> None:
    x = [punto[0] for punto in puntos]
    y = [punto[1] for punto in puntos]
    z = [punto[2] for punto in puntos]
    ax.plot(x, y, z, color=color, linewidth=3, label=etiqueta)
    ax.scatter(x, y, z, color=color, s=36)


def _dibujar_tablero_3d(ax, sistema, casilla_inicio: str, casilla_fin: str) -> None:
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    tamaño = sistema.tablero.tamaño_casilla
    origen_x = -sistema.tablero.ancho / 2
    origen_y = sistema.offset
    colores = ("#f2e9dc", "#9c6644")

    for fila in range(sistema.tablero.filas):
        for columna in range(sistema.tablero.columnas):
            x0 = origen_x + (columna * tamaño)
            y0 = origen_y + (fila * tamaño)
            vertices = [[(x0, y0, 0), (x0 + tamaño, y0, 0), (x0 + tamaño, y0 + tamaño, 0), (x0, y0 + tamaño, 0)]]

            casilla = f"{chr(ord('A') + columna)}{fila + 1}"
            color = colores[(fila + columna) % 2]
            if casilla.upper() == casilla_inicio.upper():
                color = "#8ce99a"
            elif casilla.upper() == casilla_fin.upper():
                color = "#ffa8a8"

            ax.add_collection3d(Poly3DCollection(vertices, facecolors=color, edgecolors="#3d2b1f", linewidths=0.25, alpha=0.82))

            if casilla.upper() in (casilla_inicio.upper(), casilla_fin.upper()):
                ax.text(
                    x0 + (tamaño / 2),
                    y0 + (tamaño / 2),
                    0.25,
                    casilla,
                    color="#111111",
                    fontsize=10,
                    fontweight="bold",
                    ha="center",
                    va="center",
                )


def _ajustar_limites_3d(ax, puntos: list[tuple[float, float, float]]) -> None:
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    zs = [p[2] for p in puntos]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    pad_x = max(2.0, (max_x - min_x) * 0.2)
    pad_y = max(2.0, (max_y - min_y) * 0.2)
    pad_z = max(1.2, (max_z - min_z) * 0.35)

    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min(-1.0, min_y - pad_y), max_y + pad_y)
    ax.set_zlim(0.0, max(max_z + pad_z, 4.0))
