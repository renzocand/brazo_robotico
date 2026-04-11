Plan: Juego de Ajedrez en Consola (estilo Chessmaster Game Boy)
Contexto
Se agrega un juego de ajedrez completo en consola dentro de brazo_robotico/ajedrez.py. El usuario juega como NEGRAS, la PC juega como BLANCAS. La IA usa Alpha-Beta puro (dos funciones maximo/minimo) con Quiescence Search — el mismo estilo del Chessmaster Game Boy (1989), elegido por claridad educativa. Se usa rich (ya instalado) para el rendering: colores, paneles y spinner de "pensando".

Representación de piezas en consola
Letras en español, alineamiento garantizado (sin Unicode de ajedrez que se desborda). Blancas vs Negras se distinguen por color rich + fondo de casilla:

Pieza	Símbolo	Motivo
Rey	R	Rey
Reina	r	reina (minúscula para diferenciarse de R)
Torre	T	Torre
Alfil	A	Alfil
Caballo	C	Caballo
Peón	P	Peón
Esquema de colores con rich:

Blancas (PC): bold white sobre fondo de casilla
Negras (tú): bold cyan sobre fondo de casilla
Casilla clara: fondo grey82
Casilla oscura: fondo grey37
Casilla seleccionada: fondo green (pieza elegida)
Destinos válidos: fondo yellow3 (adónde puede ir)
Casilla en jaque: fondo red (rey en peligro)
Layout del tablero (letras ASCII + rich colors):

╭─────────────────────────────────────────────╮
│          AJEDREZ TERMINAL  v1.0             │
│          Dificultad: INTERMEDIO             │
╰─────────────────────────────────────────────╯

     A   B   C   D   E   F   G   H
   ┌───┬───┬───┬───┬───┬───┬───┬───┐
 8 │ T │ C │ A │ r │ R │ A │ C │ T │  ← negras (cyan)
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 7 │ P │ P │ P │ P │ P │ P │ P │ P │
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 6 │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 5 │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 4 │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 3 │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 2 │ P │ P │ P │ P │ P │ P │ P │ P │
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 1 │ T │ C │ A │ r │ R │ A │ C │ T │  ← blancas (blanco)
   └───┴───┴───┴───┴───┴───┴───┴───┘

  PC jugó: E2 → E4   │  Capturadas: —   │  Jugada #1
  ══════════════════════════════════════════
  ● TU TURNO (Negras)
  > Jugada (ej: E7-E5) o casilla para ver opciones (E7): _
Flujo UX — Opción C híbrida
flowchart TD
    A([TU TURNO]) --> B[/"Jugada (E7-E5) o casilla (E7):"/]
    B --> C{¿Qué escribió?}
    C -->|"Solo casilla\nEj: E7"| D{¿Es pieza negra\ncon movimientos?}
    C -->|"Jugada completa\nEj: E7-E5"| G{¿Es movimiento\nlegal?}
    C -->|"'ayuda'"| H[Mostrar\nleyenda de piezas]
    C -->|"'salir'"| I([Fin del juego])
    C -->|"'tablas'"| J[Ofrecer tablas\na la PC]
    D -->|NO| K["✗ Pieza inválida\no sin movimientos"]
    D -->|SÍ| E[Redibujar tablero\ncon destinos en amarillo]
    E --> F[/"Destino (E5/E6) o ENTER\npara cancelar:"/]
    F -->|ENTER| A
    F -->|casilla| G
    G -->|NO| L["✗ Movimiento inválido\nintenta de nuevo"]
    G -->|SÍ| M[Aplicar movimiento\nActualizar estado]
    L --> B
    K --> B
    H --> B
    M --> N([TURNO PC])
Mensajes de estado (con rich):

  ⚠  [bold red]JAQUE — tu Rey está en peligro[/bold red]
  ✗  [red]Movimiento inválido, intenta de nuevo[/red]
  ✓  [green]E7 → E5 ejecutado[/green]
  ★  [bold yellow]JAQUE MATE — las Blancas ganan[/bold yellow]
Pantalla de selección de dificultad al inicio:

╭─────────────────────────────────╮
│    AJEDREZ TERMINAL  v1.0       │
│                                 │
│  Selecciona dificultad:         │
│                                 │
│   [1] Fácil       (prof. 2)    │
│   [2] Intermedio  (prof. 3)    │
│   [3] Difícil     (prof. 4)    │
│                                 │
╰─────────────────────────────────╯
Archivos involucrados
brazo_robotico/ajedrez.py — implementación completa (actualmente solo tiene def main(): pass)
brazo_robotico/tablero.py — reutilizar Tablero.casilla_a_xy() y notación A1-H8
brazo_robotico/config.py — reutilizar DIAMETRO_CASILLA = 3.0
brazo_robotico/tipos.py — reutilizar Coordenada
main.py — ya apunta a ajedrez.main(), no hay que tocarlo
requirements.txt — rich>=13.4.1 ya está listado
Arquitectura (todo en ajedrez.py)
Dataclasses de estado
@dataclass
class Pieza:
    tipo: str      # 'R','r','T','A','C','P'  (letras españolas)
    color: str     # 'W' (blancas/PC) o 'B' (negras/usuario)
    movida: bool = False   # para enroque y doble avance de peón

@dataclass
class Movimiento:
    desde: tuple[int, int]
    hasta: tuple[int, int]
    promocion: str | None = None
    es_enroque_corto: bool = False
    es_enroque_largo: bool = False
    es_en_passant: bool = False

@dataclass
class EstadoJuego:
    tablero: list[list]          # 8x8, None = casilla vacía
    turno: str                   # 'W' o 'B'
    en_passant: tuple | None     # casilla objetivo si aplica
    derechos_enroque: dict       # W_corto, W_largo, B_corto, B_largo
    medio_movimientos: int       # para regla de 50 movimientos
Índices del tablero
tablero[fila][col]  →  fila 0 = rank 1, fila 7 = rank 8, col 0 = A, col 7 = H
Coincide con Tablero.casilla_a_xy() existente.

Cómo funciona Minimax + Alpha-Beta (el algoritmo)
Concepto base
El tablero es un árbol. Cada nodo = una posición. Cada rama = un movimiento posible.

Blancas (MAX): elige el movimiento con mayor puntuación
Negras (MIN): elige el movimiento con menor puntuación
En las hojas (profundidad 0): evalúa con la función de evaluación
Diagrama de flujo — Alpha-Beta puro
flowchart TD
    START([mejor_movimiento\nprof según dificultad]) --> LOOP[Para cada mov de Blancas\nordenados: capturas primero]
    LOOP --> CALL["puntos = minimo(hijo, prof-1,\nalfa=-∞, beta=+∞)"]
    CALL --> BEST[Si puntos > mejor:\nguardar movimiento]
    BEST --> LOOP
    LOOP -->|fin| RET([retornar mejor movimiento])

    subgraph MAXIMO["maximo(estado, prof, alfa, beta) — turno Blancas"]
        MA{¿prof == 0?} -->|SÍ| MQ[quiescence\nalfa, beta]
        MA -->|NO| MM[Para cada mov Blancas]
        MM --> MC["alfa = max(alfa,\nminimo(hijo, prof-1, alfa, beta))"]
        MC --> MCUT{¿alfa ≥ beta?}
        MCUT -->|SÍ CORTE BETA| MR([retornar alfa])
        MCUT -->|NO| MM
        MM -->|fin| MR2([retornar alfa])
    end

    subgraph MINIMO["minimo(estado, prof, alfa, beta) — turno Negras"]
        NA{¿prof == 0?} -->|SÍ| NQ[quiescence\nalfa, beta]
        NA -->|NO| NM[Para cada mov Negras]
        NM --> NC["beta = min(beta,\nmaximo(hijo, prof-1, alfa, beta))"]
        NC --> NCUT{¿alfa ≥ beta?}
        NCUT -->|SÍ CORTE ALFA| NR([retornar beta])
        NCUT -->|NO| NM
        NM -->|fin| NR2([retornar beta])
    end
Quiescence Search — extensión al llegar a profundidad 0
flowchart TD
    Q([quiescence\nalfa, beta]) --> EVAL[puntos_base = evaluar estado]
    EVAL --> CHECK{¿puntos_base ≥ beta?}
    CHECK -->|SÍ CORTE| RB([retornar beta])
    CHECK -->|NO| UPD[alfa = max(alfa, puntos_base)]
    UPD --> CAPS[Para cada captura legal\nordenadas MVV-LVA]
    CAPS --> APPLY[aplicar captura]
    APPLY --> REC["puntos = -quiescence(hijo,\n-beta, -alfa)"]
    REC --> UPD2[alfa = max(alfa, puntos)]
    UPD2 --> CUT{¿alfa ≥ beta?}
    CUT -->|SÍ CORTE| RB2([retornar beta])
    CUT -->|NO| CAPS
    CAPS -->|fin| RA([retornar alfa])
Por qué Alpha-Beta es tan importante
Algoritmo	Nodos analizados (prof. 3, ~35 mov/pos)
Minimax puro	35³ = 42,875
Alpha-Beta sin ordenar	~15,000
Alpha-Beta típico (capturas primero)	~2,000–4,000
Alpha-Beta óptimo teórico	√(35³) ≈ 207
El ordenamiento MVV-LVA (capturas de pieza valiosa con pieza barata primero) es lo que acerca el caso típico al óptimo.

Función de evaluación
puntuacion = material_blancas - material_negras
           + posicional_blancas - posicional_negras

Valores: P=100  C=320  A=330  T=500  r=900  R=20000
Piece-Square Tables (PST): matrices 8×8 con bonus/penalidad por casilla:

Peón: bonus por avance y control del centro
Caballo: bonus en casillas centrales, penalidad en bordes
Alfil: diagonales largas
Torre: columnas abiertas, bonificación en 7ª fila
Reina: leve preferencia central
Rey (medio juego): penaliza exposición, premia enroque
Rey (final): premia centralización
Módulos internos
GeneradorMovimientos (clase estática)
movimientos_legales(estado, color) → filtra pseudolegales: aplica mov, verifica que rey propio no quede en jaque
movimientos_pseudolegales(estado, color) → por tipo de pieza
es_en_jaque(estado, color) → escanea ataques del oponente sobre el rey
Reglas completas: peón (doble avance, captura diagonal, en passant, promoción), caballo, alfil, torre, reina, rey + enroque
Motor — Alpha-Beta puro + Quiescence
DIFICULTAD = {'1': 2, '2': 3, '3': 4}   # profundidad por nivel

def mejor_movimiento(estado, profundidad) -> Movimiento
def maximo(estado, prof, alfa, beta) -> float   # turno Blancas
def minimo(estado, prof, alfa, beta) -> float   # turno Negras
def quiescence(estado, alfa, beta) -> float     # solo capturas
def evaluar(estado) -> float                    # material + PST
def aplicar_movimiento(estado, mov) -> EstadoJuego  # retorna copia nueva
Renderer — usa rich
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.live import Live    # para spinner de "pensando"

def dibujar_tablero(estado, casilla_sel=None, movs_validos=None)
def dibujar_header(dificultad)
def dibujar_estado(turno, ultimo_mov_pc, capturadas)
def mostrar_pensando()         # spinner rich mientras PC calcula
def mostrar_mensaje(texto, tipo)   # info / warn / error / win
def pedir_jugada(prompt) -> str
JuegoAjedrez — Bucle de juego
iniciar()
  └─ elegir_dificultad()
  └─ PC abre (turno 'W' primero)
  └─ LOOP:
       verificar_fin_juego() → jaque_mate / tablas / None
       turno 'W' → _turno_pc(profundidad)
       turno 'B' → _turno_jugador()
Turno jugador (flujo híbrido Opción C):

Si está en jaque → mostrar advertencia roja
Leer entrada: puede ser E7-E5 (jugada completa) o E7 (ver opciones)
Si es casilla sola → redibujar con destinos en amarillo → pedir destino
Validar movimiento → aplicar o mostrar error → repetir si inválido
Turno PC:

Mostrar spinner rich.live mientras calcula
Motor.mejor_movimiento(estado, profundidad)
Aplicar movimiento → imprimir "PC jugó: E2 → E4"
Orden de implementación
Dataclasses + posición inicial (Pieza, Movimiento, EstadoJuego, _posicion_inicial())
aplicar_movimiento() — retorna copia nueva del estado, maneja en passant, enroque, promoción
Generación pseudolegal — peón, caballo, rey (sin enroque aún)
es_en_jaque() + movimientos_legales() — filtro apply-and-check
Piezas deslizantes + enroque — alfil, torre, reina, enroque completo
Detección de fin de juego — jaque mate, tablas, material insuficiente, regla 50 mov.
Renderer — tablero con rich, colores por casilla, highlights de selección
Motor — Alpha-Beta puro + Quiescence + PST + MVV-LVA
JuegoAjedrez — bucle completo, menú de dificultad, flujo híbrido
main() — arranque, integración con Tablero.casilla_a_xy() para coordenadas del brazo
Integración con el sistema existente
Al final de cada movimiento mostrar coordenadas para el brazo robótico:

from brazo_robotico.tablero import Tablero
from brazo_robotico.config import DIAMETRO_CASILLA
coord = Tablero(tamaño_casilla=DIAMETRO_CASILLA).casilla_a_xy(casilla)
# imprime: "Brazo: E7 → (12.0, 18.0) cm"
Verificación
python main.py → menú de dificultad → tablero con colores rich
Posición inicial: 20 movimientos legales para ambos colores
Seleccionar pieza → destinos resaltados en amarillo
Jugada completa E7-E5 → ejecuta sin pasos intermedios
PC responde con spinner mientras piensa (< 5 seg en dificultad 2-3)
Jaque mostrado en rojo, jaque mate con panel final
Funciona en Windows 11 terminal (rich maneja la codificación)