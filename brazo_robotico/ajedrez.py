# brazo_robotico/ajedrez.py
# Juego de ajedrez en consola — estilo Chessmaster Game Boy (1989)
# IA: Alpha-Beta puro (maximo/minimo) + Quiescence Search
# Rendering: rich

import copy
import time
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner

from brazo_robotico.sistema import SistemaBrazo
from brazo_robotico.tipos import AngulosServo
from brazo_robotico.arduino_link import ArduinoLink
from brazo_robotico.config import (
    ARDUINO_HABILITADO,
    ARDUINO_PUERTO,
    ARDUINO_BAUDIOS,
    ARDUINO_MS_POR_PASO,
    ARDUINO_PAUSA_AGARRE_MS,
    ARDUINO_PARKED_BASE,
    ARDUINO_PARKED_BRAZO1,
    ARDUINO_PARKED_BRAZO2,
    PINZA_ABIERTA,
    PINZA_CERRADA,
)

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────

DIFICULTAD = {'1': 2, '2': 3, '3': 4}

VALORES_PIEZA = {
    'P': 100,
    'C': 320,
    'A': 330,
    'T': 500,
    'r': 900,
    'R': 20000,
}

# ──────────────────────────────────────────────
# PIECE-SQUARE TABLES  (indexadas rank8→rank1)
# Para Blancas: idx = (7-fila)*8 + col
# Para Negras:  idx = fila*8 + col
# ──────────────────────────────────────────────

PST_PEON = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PST_CABALLO = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

PST_ALFIL = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

PST_TORRE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

PST_REINA = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

PST_REY = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

PST_MAP = {
    'P': PST_PEON,
    'C': PST_CABALLO,
    'A': PST_ALFIL,
    'T': PST_TORRE,
    'r': PST_REINA,
    'R': PST_REY,
}

# ──────────────────────────────────────────────
# DATACLASSES
# ──────────────────────────────────────────────

@dataclass
class Pieza:
    tipo: str        # 'R','r','T','A','C','P'  (letras españolas)
    color: str       # 'W' (blancas/PC) o 'B' (negras/usuario)
    movida: bool = False


@dataclass
class Movimiento:
    desde: tuple
    hasta: tuple
    promocion: Optional[str] = None
    es_enroque_corto: bool = False
    es_enroque_largo: bool = False
    es_en_passant: bool = False


@dataclass
class EstadoJuego:
    tablero: list
    turno: str                       # 'W' o 'B'
    en_passant: Optional[tuple] = None
    derechos_enroque: dict = field(default_factory=lambda: {
        'W_corto': True, 'W_largo': True,
        'B_corto': True, 'B_largo': True,
    })
    medio_movimientos: int = 0       # para regla de 50 movimientos


# ──────────────────────────────────────────────
# POSICIÓN INICIAL
# ──────────────────────────────────────────────

def _posicion_inicial() -> list:
    def P(tipo, color):
        return Pieza(tipo, color)

    back = ['T', 'C', 'A', 'r', 'R', 'A', 'C', 'T']
    tablero = [[None] * 8 for _ in range(8)]

    for col, tipo in enumerate(back):
        tablero[0][col] = P(tipo, 'W')   # rank 1 — Blancas
        tablero[7][col] = P(tipo, 'B')   # rank 8 — Negras

    for col in range(8):
        tablero[1][col] = P('P', 'W')    # rank 2
        tablero[6][col] = P('P', 'B')    # rank 7

    return tablero


# ──────────────────────────────────────────────
# APLICAR MOVIMIENTO  (retorna copia nueva, nunca muta)
# ──────────────────────────────────────────────

def aplicar_movimiento(estado: EstadoJuego, mov: Movimiento) -> EstadoJuego:
    nuevo_tablero = [
        [copy.copy(p) if p else None for p in fila]
        for fila in estado.tablero
    ]
    derechos = dict(estado.derechos_enroque)

    f_desde, c_desde = mov.desde
    f_hasta, c_hasta = mov.hasta
    pieza = nuevo_tablero[f_desde][c_desde]

    pieza.movida = True
    nuevo_tablero[f_hasta][c_hasta] = pieza
    nuevo_tablero[f_desde][c_desde] = None

    # En passant: eliminar el peón capturado (misma fila que el atacante, columna destino)
    if mov.es_en_passant:
        nuevo_tablero[f_desde][c_hasta] = None

    # Promoción: reemplazar peón por pieza elegida
    if mov.promocion:
        nuevo_tablero[f_hasta][c_hasta] = Pieza(mov.promocion, pieza.color, True)

    # Enroque corto: mover torre de col 7 a col 5
    if mov.es_enroque_corto:
        torre = nuevo_tablero[f_desde][7]
        if torre:
            torre.movida = True
        nuevo_tablero[f_desde][5] = torre
        nuevo_tablero[f_desde][7] = None

    # Enroque largo: mover torre de col 0 a col 3
    elif mov.es_enroque_largo:
        torre = nuevo_tablero[f_desde][0]
        if torre:
            torre.movida = True
        nuevo_tablero[f_desde][3] = torre
        nuevo_tablero[f_desde][0] = None

    # Actualizar derechos de enroque si rey o torre se movieron
    if pieza.tipo == 'R':
        if pieza.color == 'W':
            derechos['W_corto'] = False
            derechos['W_largo'] = False
        else:
            derechos['B_corto'] = False
            derechos['B_largo'] = False
    if pieza.tipo == 'T':
        if f_desde == 0 and c_desde == 0:
            derechos['W_largo'] = False
        if f_desde == 0 and c_desde == 7:
            derechos['W_corto'] = False
        if f_desde == 7 and c_desde == 0:
            derechos['B_largo'] = False
        if f_desde == 7 and c_desde == 7:
            derechos['B_corto'] = False

    # Si se captura una torre, revocar su derecho
    if f_hasta == 0 and c_hasta == 0:
        derechos['W_largo'] = False
    if f_hasta == 0 and c_hasta == 7:
        derechos['W_corto'] = False
    if f_hasta == 7 and c_hasta == 0:
        derechos['B_largo'] = False
    if f_hasta == 7 and c_hasta == 7:
        derechos['B_corto'] = False

    # Objetivo de en passant para el próximo turno
    nuevo_en_passant = None
    if pieza.tipo == 'P' and abs(f_hasta - f_desde) == 2:
        nuevo_en_passant = ((f_desde + f_hasta) // 2, c_desde)

    # Contador de 50 movimientos
    captura = (estado.tablero[f_hasta][c_hasta] is not None) or mov.es_en_passant
    nuevo_medio_mov = 0 if (pieza.tipo == 'P' or captura) else estado.medio_movimientos + 1

    return EstadoJuego(
        tablero=nuevo_tablero,
        turno='B' if estado.turno == 'W' else 'W',
        en_passant=nuevo_en_passant,
        derechos_enroque=derechos,
        medio_movimientos=nuevo_medio_mov,
    )


# ──────────────────────────────────────────────
# GENERACIÓN DE MOVIMIENTOS
# ──────────────────────────────────────────────

def _en_tablero(f, c):
    return 0 <= f < 8 and 0 <= c < 8


def _mover_peon(estado: EstadoJuego, fila: int, col: int) -> list:
    movs = []
    pieza = estado.tablero[fila][col]
    color = pieza.color
    dir_ = 1 if color == 'W' else -1
    fila_inicio = 1 if color == 'W' else 6
    fila_promo = 7 if color == 'W' else 0

    # Avance simple
    nf = fila + dir_
    if _en_tablero(nf, col) and estado.tablero[nf][col] is None:
        if nf == fila_promo:
            for promo in ['r', 'T', 'A', 'C']:
                movs.append(Movimiento((fila, col), (nf, col), promocion=promo))
        else:
            movs.append(Movimiento((fila, col), (nf, col)))
        # Doble avance desde fila inicial
        nf2 = fila + 2 * dir_
        if fila == fila_inicio and _en_tablero(nf2, col) and estado.tablero[nf2][col] is None:
            movs.append(Movimiento((fila, col), (nf2, col)))

    # Capturas diagonales + en passant
    for dc in [-1, 1]:
        nc = col + dc
        nf = fila + dir_
        if not _en_tablero(nf, nc):
            continue
        objetivo = estado.tablero[nf][nc]
        if objetivo is not None and objetivo.color != color:
            if nf == fila_promo:
                for promo in ['r', 'T', 'A', 'C']:
                    movs.append(Movimiento((fila, col), (nf, nc), promocion=promo))
            else:
                movs.append(Movimiento((fila, col), (nf, nc)))
        elif estado.en_passant == (nf, nc):
            movs.append(Movimiento((fila, col), (nf, nc), es_en_passant=True))

    return movs


def _mover_caballo(estado: EstadoJuego, fila: int, col: int) -> list:
    movs = []
    pieza = estado.tablero[fila][col]
    for df, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nf, nc = fila + df, col + dc
        if not _en_tablero(nf, nc):
            continue
        objetivo = estado.tablero[nf][nc]
        if objetivo is None or objetivo.color != pieza.color:
            movs.append(Movimiento((fila, col), (nf, nc)))
    return movs


def _mover_deslizante(estado: EstadoJuego, fila: int, col: int, direcciones: list) -> list:
    movs = []
    pieza = estado.tablero[fila][col]
    for df, dc in direcciones:
        nf, nc = fila + df, col + dc
        while _en_tablero(nf, nc):
            objetivo = estado.tablero[nf][nc]
            if objetivo is None:
                movs.append(Movimiento((fila, col), (nf, nc)))
            elif objetivo.color != pieza.color:
                movs.append(Movimiento((fila, col), (nf, nc)))
                break
            else:
                break
            nf += df
            nc += dc
    return movs


def _mover_alfil(estado, fila, col):
    return _mover_deslizante(estado, fila, col, [(-1,-1),(-1,1),(1,-1),(1,1)])


def _mover_torre(estado, fila, col):
    return _mover_deslizante(estado, fila, col, [(-1,0),(1,0),(0,-1),(0,1)])


def _mover_reina(estado, fila, col):
    return _mover_deslizante(
        estado, fila, col,
        [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]
    )


def _mover_rey(estado: EstadoJuego, fila: int, col: int) -> list:
    movs = []
    pieza = estado.tablero[fila][col]
    color = pieza.color

    for df in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if df == 0 and dc == 0:
                continue
            nf, nc = fila + df, col + dc
            if not _en_tablero(nf, nc):
                continue
            objetivo = estado.tablero[nf][nc]
            if objetivo is None or objetivo.color != color:
                movs.append(Movimiento((fila, col), (nf, nc)))

    # Enroque (condiciones geométricas; las condiciones de jaque se verifican en movimientos_legales)
    if not pieza.movida:
        fila_base = 0 if color == 'W' else 7
        if fila == fila_base and col == 4:
            # Corto (lado del rey)
            if estado.derechos_enroque.get(f'{color}_corto'):
                torre = estado.tablero[fila_base][7]
                if (torre and torre.tipo == 'T' and not torre.movida
                        and estado.tablero[fila_base][5] is None
                        and estado.tablero[fila_base][6] is None):
                    movs.append(Movimiento(
                        (fila, col), (fila_base, 6), es_enroque_corto=True
                    ))
            # Largo (lado de la reina)
            if estado.derechos_enroque.get(f'{color}_largo'):
                torre = estado.tablero[fila_base][0]
                if (torre and torre.tipo == 'T' and not torre.movida
                        and estado.tablero[fila_base][1] is None
                        and estado.tablero[fila_base][2] is None
                        and estado.tablero[fila_base][3] is None):
                    movs.append(Movimiento(
                        (fila, col), (fila_base, 2), es_enroque_largo=True
                    ))

    return movs


_GENERADORES = {
    'P': _mover_peon,
    'C': _mover_caballo,
    'A': _mover_alfil,
    'T': _mover_torre,
    'r': _mover_reina,
    'R': _mover_rey,
}


def movimientos_pseudolegales(estado: EstadoJuego, color: str) -> list:
    movs = []
    for fila in range(8):
        for col in range(8):
            p = estado.tablero[fila][col]
            if p and p.color == color:
                movs.extend(_GENERADORES[p.tipo](estado, fila, col))
    return movs


# ──────────────────────────────────────────────
# DETECCIÓN DE JAQUE Y MOVIMIENTOS LEGALES
# ──────────────────────────────────────────────

def _encontrar_rey(estado: EstadoJuego, color: str) -> Optional[tuple]:
    for fila in range(8):
        for col in range(8):
            p = estado.tablero[fila][col]
            if p and p.tipo == 'R' and p.color == color:
                return (fila, col)
    return None


def es_en_jaque(estado: EstadoJuego, color: str) -> bool:
    pos_rey = _encontrar_rey(estado, color)
    if pos_rey is None:
        return False
    oponente = 'B' if color == 'W' else 'W'
    return any(m.hasta == pos_rey for m in movimientos_pseudolegales(estado, oponente))


def _estado_con_rey_en(estado: EstadoJuego, fila_rey: int, col_origen: int, col_dest: int) -> EstadoJuego:
    """Crea copia del estado con el rey movido a col_dest (para validar enroque)."""
    nuevo_tablero = [
        [copy.copy(p) if p else None for p in f]
        for f in estado.tablero
    ]
    rey = nuevo_tablero[fila_rey][col_origen]
    nuevo_tablero[fila_rey][col_dest] = copy.copy(rey)
    nuevo_tablero[fila_rey][col_origen] = None
    return EstadoJuego(
        tablero=nuevo_tablero,
        turno=estado.turno,
        en_passant=estado.en_passant,
        derechos_enroque=dict(estado.derechos_enroque),
        medio_movimientos=estado.medio_movimientos,
    )


def movimientos_legales(estado: EstadoJuego, color: str) -> list:
    legales = []
    for mov in movimientos_pseudolegales(estado, color):
        # No se puede enrocar estando en jaque
        if (mov.es_enroque_corto or mov.es_enroque_largo) and es_en_jaque(estado, color):
            continue

        nuevo = aplicar_movimiento(estado, mov)
        if es_en_jaque(nuevo, color):
            continue

        # El rey no puede pasar por casilla atacada durante el enroque
        if mov.es_enroque_corto or mov.es_enroque_largo:
            f, c = mov.desde
            col_paso = 5 if mov.es_enroque_corto else 3
            estado_paso = _estado_con_rey_en(estado, f, c, col_paso)
            if es_en_jaque(estado_paso, color):
                continue

        legales.append(mov)
    return legales


# ──────────────────────────────────────────────
# FIN DE JUEGO
# ──────────────────────────────────────────────

def verificar_fin(estado: EstadoJuego, color: str) -> Optional[str]:
    """Retorna 'jaque_mate', 'ahogado', 'material' o '50_movimientos', o None."""
    movs = movimientos_legales(estado, color)
    if not movs:
        return 'jaque_mate' if es_en_jaque(estado, color) else 'ahogado'

    if estado.medio_movimientos >= 100:
        return '50_movimientos'

    # Material insuficiente: solo quedan reyes, o rey + alfil/caballo vs rey
    piezas = [
        p for fila in estado.tablero for p in fila
        if p and p.tipo != 'R'
    ]
    if len(piezas) == 0:
        return 'material'
    if len(piezas) == 1 and piezas[0].tipo in ('C', 'A'):
        return 'material'

    return None


# ──────────────────────────────────────────────
# EVALUACIÓN + PST
# ──────────────────────────────────────────────

def _pst_valor(pieza: Pieza, fila: int, col: int) -> int:
    tabla = PST_MAP.get(pieza.tipo)
    if tabla is None:
        return 0
    idx = (7 - fila) * 8 + col if pieza.color == 'W' else fila * 8 + col
    return tabla[idx]


def evaluar(estado: EstadoJuego) -> float:
    """Positivo = bueno para Blancas (PC)."""
    score = 0
    for fila in range(8):
        for col in range(8):
            p = estado.tablero[fila][col]
            if p is None:
                continue
            valor = VALORES_PIEZA[p.tipo] + _pst_valor(p, fila, col)
            score += valor if p.color == 'W' else -valor
    return score


# ──────────────────────────────────────────────
# ORDENAMIENTO MVV-LVA (capturas más valiosas primero)
# ──────────────────────────────────────────────

def _prioridad(mov: Movimiento, estado: EstadoJuego) -> float:
    fh, ch = mov.hasta
    fd, cd = mov.desde
    victima = estado.tablero[fh][ch]
    atacante = estado.tablero[fd][cd]
    if victima and atacante:
        return VALORES_PIEZA[victima.tipo] - VALORES_PIEZA[atacante.tipo] / 10.0
    if mov.promocion:
        return VALORES_PIEZA.get(mov.promocion, 0)
    return 0.0


def _ordenar(movs: list, estado: EstadoJuego) -> list:
    return sorted(movs, key=lambda m: _prioridad(m, estado), reverse=True)


# ──────────────────────────────────────────────
# QUIESCENCE SEARCH
# ──────────────────────────────────────────────

def _quiescence(estado: EstadoJuego, alfa: float, beta: float) -> float:
    """Extiende la búsqueda solo con capturas para evitar el efecto horizonte."""
    color = estado.turno

    score_base = evaluar(estado)

    if color == 'W':   # Maximizando
        if score_base >= beta:
            return beta
        if score_base > alfa:
            alfa = score_base

        capturas = [
            m for m in movimientos_pseudolegales(estado, 'W')
            if estado.tablero[m.hasta[0]][m.hasta[1]] is not None or m.es_en_passant
        ]
        for mov in _ordenar(capturas, estado):
            nuevo = aplicar_movimiento(estado, mov)
            if es_en_jaque(nuevo, 'W'):
                continue
            puntos = _quiescence(nuevo, alfa, beta)
            if puntos > alfa:
                alfa = puntos
            if alfa >= beta:
                break
        return alfa

    else:               # Minimizando
        if score_base <= alfa:
            return alfa
        if score_base < beta:
            beta = score_base

        capturas = [
            m for m in movimientos_pseudolegales(estado, 'B')
            if estado.tablero[m.hasta[0]][m.hasta[1]] is not None or m.es_en_passant
        ]
        for mov in _ordenar(capturas, estado):
            nuevo = aplicar_movimiento(estado, mov)
            if es_en_jaque(nuevo, 'B'):
                continue
            puntos = _quiescence(nuevo, alfa, beta)
            if puntos < beta:
                beta = puntos
            if alfa >= beta:
                break
        return beta


# ──────────────────────────────────────────────
# ALPHA-BETA PURO  (maximo / minimo)
# ──────────────────────────────────────────────

def _maximo(estado: EstadoJuego, prof: int, alfa: float, beta: float) -> float:
    """Turno Blancas (PC) — maximiza la puntuación."""
    if prof == 0:
        return _quiescence(estado, alfa, beta)

    movs = movimientos_legales(estado, 'W')
    if not movs:
        return -99999 if es_en_jaque(estado, 'W') else 0

    for mov in _ordenar(movs, estado):
        nuevo = aplicar_movimiento(estado, mov)
        puntos = _minimo(nuevo, prof - 1, alfa, beta)
        if puntos > alfa:
            alfa = puntos
        if alfa >= beta:
            break   # CORTE BETA
    return alfa


def _minimo(estado: EstadoJuego, prof: int, alfa: float, beta: float) -> float:
    """Turno Negras (jugador) — minimiza la puntuación."""
    if prof == 0:
        return _quiescence(estado, alfa, beta)

    movs = movimientos_legales(estado, 'B')
    if not movs:
        return 99999 if es_en_jaque(estado, 'B') else 0

    for mov in _ordenar(movs, estado):
        nuevo = aplicar_movimiento(estado, mov)
        puntos = _maximo(nuevo, prof - 1, alfa, beta)
        if puntos < beta:
            beta = puntos
        if alfa >= beta:
            break   # CORTE ALFA
    return beta


def mejor_movimiento(estado: EstadoJuego, profundidad: int) -> Optional[Movimiento]:
    """Elige el mejor movimiento para Blancas (PC)."""
    mejor = None
    mejor_puntos = -float('inf')
    alfa = -float('inf')
    beta = float('inf')

    movs = movimientos_legales(estado, 'W')
    if not movs:
        return None

    for mov in _ordenar(movs, estado):
        nuevo = aplicar_movimiento(estado, mov)
        puntos = _minimo(nuevo, profundidad - 1, alfa, beta)
        if puntos > mejor_puntos:
            mejor_puntos = puntos
            mejor = mov
        if puntos > alfa:
            alfa = puntos

    return mejor


# ──────────────────────────────────────────────
# UTILIDADES DE NOTACIÓN
# ──────────────────────────────────────────────

def casilla_a_indices(casilla: str) -> Optional[tuple]:
    """'E7' → (6, 4). Retorna None si inválida."""
    if not casilla or len(casilla) != 2:
        return None
    col = ord(casilla[0].upper()) - ord('A')
    try:
        fila = int(casilla[1]) - 1
    except ValueError:
        return None
    if not (0 <= col < 8 and 0 <= fila < 8):
        return None
    return (fila, col)


def indices_a_casilla(fila: int, col: int) -> str:
    """(6, 4) → 'E7'."""
    return chr(ord('A') + col) + str(fila + 1)


# ──────────────────────────────────────────────
# RENDERER  (usa rich)
# ──────────────────────────────────────────────

console = Console()

_NOMBRE_PIEZA = {
    'R': 'Rey', 'r': 'Reina', 'T': 'Torre',
    'A': 'Alfil', 'C': 'Caballo', 'P': 'Peón',
}


def _bg_casilla(fila: int, col: int,
                sel: Optional[tuple],
                dests: set,
                jaque_pos: Optional[tuple],
                ultimo_mov: set) -> str:
    pos = (fila, col)
    if pos == sel:
        return 'on green4'
    if pos in dests:
        return 'on dark_goldenrod'
    if pos == jaque_pos:
        return 'on red3'
    if pos in ultimo_mov:
        return 'on navy_blue'
    return 'on grey15' if (fila + col) % 2 == 0 else 'on grey30'


def dibujar_tablero(estado: EstadoJuego,
                    sel: Optional[tuple] = None,
                    dests: Optional[set] = None,
                    ultimo_mov: Optional[set] = None):
    jaque_pos = None
    if es_en_jaque(estado, 'B'):
        jaque_pos = _encontrar_rey(estado, 'B')
    elif es_en_jaque(estado, 'W'):
        jaque_pos = _encontrar_rey(estado, 'W')

    dests = dests or set()
    ultimo_mov = ultimo_mov or set()

    console.print()
    console.print("       A   B   C   D   E   F   G   H  ")
    console.print("     ┌───┬───┬───┬───┬───┬───┬───┬───┐")

    for fila in range(7, -1, -1):
        rank = fila + 1
        linea = Text(f"   {rank} │")
        for col in range(8):
            bg = _bg_casilla(fila, col, sel, dests, jaque_pos, ultimo_mov)
            p = estado.tablero[fila][col]
            if p:
                fg = 'bold bright_white' if p.color == 'W' else 'bold bright_cyan'
                linea.append(f" {p.tipo} ", style=f"{fg} {bg}")
            else:
                dot = '·' if (fila + col) % 2 == 1 else ' '
                linea.append(f" {dot} ", style=f"dim {bg}")
            linea.append("│")
        console.print(linea)
        if fila > 0:
            console.print("     ├───┼───┼───┼───┼───┼───┼───┼───┤")

    console.print("     └───┴───┴───┴───┴───┴───┴───┴───┘")
    console.print()


# ──────────────────────────────────────────────
# JUEGO PRINCIPAL
# ──────────────────────────────────────────────

class JuegoAjedrez:
    def __init__(self):
        self.estado: Optional[EstadoJuego] = None
        self.profundidad: int = 2
        self.ultimo_mov_pc: Optional[str] = None
        self.ultimo_mov_pc_casillas: set = set()   # {desde, hasta} para resaltar en tablero
        self.capturadas_por_ti: list = []    # piezas blancas capturadas por el jugador
        self.capturadas_por_pc: list = []    # piezas negras capturadas por la PC
        self.jugada_num: int = 1
        self._sistema_brazo = SistemaBrazo()
        # Última secuencia de servos calculada — la que se mandaría al Arduino
        self.ultima_secuencia_servos: Optional[dict] = None
        self._arduino: Optional[ArduinoLink] = None

    # ── Inicio ──────────────────────────────

    def iniciar(self):
        console.clear()
        self._bienvenida()
        self.profundidad = self._elegir_dificultad()
        self._inicializar_arduino()
        self.estado = EstadoJuego(
            tablero=_posicion_inicial(),
            turno='W',   # PC (Blancas) abre siempre
        )
        try:
            self._bucle()
        finally:
            if self._arduino is not None and self._arduino.conectado:
                self._arduino.cerrar()

    def _inicializar_arduino(self):
        """Si está habilitado, intenta conectar con el Arduino. Si falla, sigue en modo simulación."""
        if not ARDUINO_HABILITADO:
            console.print("  [dim]Modo simulación (Arduino deshabilitado en config.py)[/dim]")
            return

        puerto = ARDUINO_PUERTO or ArduinoLink.detectar_puerto()
        if puerto is None:
            console.print("  [yellow]⚠ No se detectó ningún Arduino. Se sigue en modo simulación.[/yellow]")
            return

        try:
            link = ArduinoLink(puerto=puerto, baudios=ARDUINO_BAUDIOS)
            link.conectar()
            if link.ping():
                self._arduino = link
                console.print(f"  [green]✓ Arduino conectado en {puerto}[/green]")
            else:
                console.print(f"  [yellow]⚠ Arduino en {puerto} no respondió a PING. Modo simulación.[/yellow]")
                link.cerrar()
        except Exception as e:
            console.print(f"  [yellow]⚠ Error abriendo {puerto}: {e}. Modo simulación.[/yellow]")

    def _bienvenida(self):
        console.print(Panel(
            Align.center(
                "[bold cyan]AJEDREZ TERMINAL  v1.0[/bold cyan]\n"
                "[dim]Estilo Chessmaster · Game Boy · 1989[/dim]\n\n"
                "[white]Tú[/white] = [bold cyan]Negras[/bold cyan]   │   "
                "[white]PC[/white] = [bold white]Blancas[/bold white]"
            ),
            border_style="cyan",
            padding=(1, 4),
        ))

    def _elegir_dificultad(self) -> int:
        console.print(Panel(
            "  [bold]Selecciona dificultad:[/bold]\n\n"
            "   [cyan][1][/cyan] Fácil       — PC ve 2 jugadas\n"
            "   [cyan][2][/cyan] Intermedio  — PC ve 3 jugadas\n"
            "   [cyan][3][/cyan] Difícil     — PC ve 4 jugadas\n",
            border_style="cyan",
        ))
        while True:
            op = console.input("  Opción [cyan](1/2/3)[/cyan]: ").strip()
            if op in DIFICULTAD:
                return DIFICULTAD[op]
            console.print("  [red]Opción inválida, elige 1, 2 o 3[/red]")

    # ── Bucle principal ──────────────────────

    def _bucle(self):
        while True:
            console.clear()
            self._dibujar_pantalla()

            resultado = verificar_fin(self.estado, self.estado.turno)
            if resultado:
                self._fin(resultado)
                break

            if self.estado.turno == 'W':
                self._turno_pc()
            else:
                self._turno_jugador()
                self.jugada_num += 1

    # ── Pantalla ─────────────────────────────

    def _dibujar_pantalla(self, sel=None, dests=None):
        dif_txt = {2: 'FÁCIL', 3: 'INTERMEDIO', 4: 'DIFÍCIL'}.get(self.profundidad, '')
        turno_txt = (
            "[bold cyan]TÚ — NEGRAS[/bold cyan]"
            if self.estado.turno == 'B'
            else "[bold white]PC — BLANCAS[/bold white]"
        )
        console.print(Panel(
            Align.center(
                f"[bold]AJEDREZ TERMINAL  v1.0[/bold]  │  "
                f"Dificultad: [yellow]{dif_txt}[/yellow]  │  "
                f"Jugada: [yellow]{self.jugada_num}[/yellow]"
            ),
            border_style="cyan",
        ))

        dibujar_tablero(self.estado, sel, dests, self.ultimo_mov_pc_casillas)

        cap_ti = ' '.join(p.tipo for p in self.capturadas_por_ti) or '—'
        cap_pc = ' '.join(p.tipo for p in self.capturadas_por_pc) or '—'
        ult = f"PC jugó: [yellow]{self.ultimo_mov_pc}[/yellow]" if self.ultimo_mov_pc else "[dim]PC no ha jugado aún[/dim]"

        console.print(f"  {ult}")
        console.print(
            f"  Capturadas por [cyan]ti[/cyan]: [cyan]{cap_ti}[/cyan]   │   "
            f"Capturadas por [white]PC[/white]: [white]{cap_pc}[/white]"
        )
        console.rule(turno_txt, style="dim")

    # ── Brazo robótico (cinemática + servos) ─────────────

    def _emitir_movimiento_brazo(self, desde: str, hasta: str, autor: str) -> None:
        """
        Calcula y muestra los ángulos de servos para el movimiento desde→hasta.
        Esta es la información que se enviará al Arduino.
        """
        try:
            servos_desde = self._calcular_servos(desde)
            servos_hasta = self._calcular_servos(hasta)
        except ValueError as e:
            console.print(f"  [yellow]⚠ Brazo: {e}[/yellow]")
            self.ultima_secuencia_servos = None
            return

        self.ultima_secuencia_servos = {
            'autor': autor,
            'desde': desde,
            'hasta': hasta,
            'servos_desde': servos_desde,
            'servos_hasta': servos_hasta,
        }

        # Línea CSV lista para enviar al Arduino (base,b1,b2 origen | base,b1,b2 destino)
        csv = (
            f"{servos_desde.base:.1f},{servos_desde.brazo1:.1f},{servos_desde.brazo2:.1f}|"
            f"{servos_hasta.base:.1f},{servos_hasta.brazo1:.1f},{servos_hasta.brazo2:.1f}"
        )
        console.print(
            f"\n  [bold cyan]Brazo robótico — {autor}: {desde} → {hasta}[/bold cyan]"
        )
        console.print(f"  [dim]→ Arduino: {csv}[/dim]")

        # Si el Arduino está conectado, enviar primero (no bloquea)
        arduino_activo = self._arduino is not None and self._arduino.conectado
        if arduino_activo:
            try:
                self._arduino.enviar_sin_esperar(servos_desde, servos_hasta)
            except Exception as e:
                console.print(f"  [red]✗ Error enviando al Arduino: {e}[/red]")
                arduino_activo = False

        # Animar el movimiento mientras esperamos OK del Arduino
        respuesta = self._animar_brazo(servos_desde, servos_hasta, arduino_activo)

        if arduino_activo:
            if respuesta.startswith("OK"):
                console.print("  [green]✓ Brazo: movimiento completado[/green]")
            elif respuesta.startswith("ERR"):
                console.print(f"  [red]✗ Brazo: {respuesta}[/red]")
            else:
                console.print("  [yellow]⚠ Brazo: sin confirmación (timeout)[/yellow]")

    def _animar_brazo(
        self,
        servos_desde: AngulosServo,
        servos_hasta: AngulosServo,
        esperar_arduino: bool,
    ) -> str:
        """
        Anima la tabla de ángulos en tiempo real, simulando el recorrido del
        brazo según los tiempos del sketch (MS_POR_PASO + PAUSA_AGARRE).
        Si esperar_arduino=True, también escucha el puerto serie y termina
        cuando llega "OK"/"ERR". Devuelve la respuesta del Arduino o "".
        """
        PARKED = (ARDUINO_PARKED_BASE, ARDUINO_PARKED_BRAZO1, ARDUINO_PARKED_BRAZO2)
        ms_paso = ARDUINO_MS_POR_PASO / 1000.0
        pausa = ARDUINO_PAUSA_AGARRE_MS / 1000.0

        desde_t = (servos_desde.base, servos_desde.brazo1, servos_desde.brazo2)
        hasta_t = (servos_hasta.base, servos_hasta.brazo1, servos_hasta.brazo2)

        def duracion(a: tuple, b: tuple) -> float:
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2])) * ms_paso

        # (etiqueta, ángulos_inicio, ángulos_fin, duración_seg, pinza_estado)
        fases = [
            ("Yendo a recoger", PARKED, desde_t, duracion(PARKED, desde_t), "abierta"),
            ("Agarrando pieza", desde_t, desde_t, pausa, f"cerrando ({PINZA_CERRADA:.0f}°)"),
            ("Yendo a soltar", desde_t, hasta_t, duracion(desde_t, hasta_t), "cerrada"),
            ("Soltando pieza", hasta_t, hasta_t, pausa, f"abriendo ({PINZA_ABIERTA:.0f}°)"),
            ("Volviendo a parked", hasta_t, PARKED, duracion(hasta_t, PARKED), "abierta"),
        ]
        duracion_total = sum(f[3] for f in fases) + 0.2

        def angulos_en(t: float):
            acum = 0.0
            for label, ai, af, d, pinza in fases:
                if t < acum + d:
                    p = (t - acum) / d if d > 0 else 1.0
                    p = min(max(p, 0.0), 1.0)
                    return (
                        (ai[0] + (af[0] - ai[0]) * p,
                         ai[1] + (af[1] - ai[1]) * p,
                         ai[2] + (af[2] - ai[2]) * p),
                        label, pinza, p,
                    )
                acum += d
            return PARKED, "Completado", f"cerrada ({PINZA_CERRADA:.0f}°)", 1.0

        def render(angulos, fase, pinza, progreso, terminado=False):
            tabla = Table(
                border_style="green" if terminado else "cyan",
                show_header=True,
                header_style="bold cyan",
            )
            tabla.add_column("Fase", justify="left")
            tabla.add_column("Servo Base", justify="right")
            tabla.add_column("Servo Brazo 1", justify="right")
            tabla.add_column("Servo Brazo 2", justify="right")
            tabla.add_column("Pinza", justify="center")
            barra = "█" * int(progreso * 10) + "░" * (10 - int(progreso * 10))
            etiqueta = f"{barra} {fase}"
            tabla.add_row(
                etiqueta,
                f"{angulos[0]:6.1f}°",
                f"{angulos[1]:6.1f}°",
                f"{angulos[2]:6.1f}°",
                pinza,
            )
            return tabla

        respuesta = ""
        inicio = time.monotonic()
        timeout_total = max(duracion_total + 5.0, 30.0)  # margen por si el Arduino tarda

        with Live(
            render(PARKED, "Iniciando...", "—", 0.0),
            console=console,
            refresh_per_second=20,
            transient=False,
        ) as live:
            while True:
                elapsed = time.monotonic() - inicio
                ang, fase, pinza, prog = angulos_en(elapsed)
                live.update(render(ang, fase, pinza, prog))

                if esperar_arduino:
                    linea = self._arduino.leer_respuesta_no_bloqueante()
                    if linea and (linea.startswith("OK") or linea.startswith("ERR")):
                        respuesta = linea
                        break
                    if elapsed > timeout_total:
                        break
                else:
                    if elapsed >= duracion_total:
                        break

                time.sleep(0.05)

            # Estado final ya fijo
            live.update(render(PARKED, "Completado", f"cerrada ({PINZA_CERRADA:.0f}°)", 1.0, terminado=True))

        return respuesta

    def _calcular_servos(self, casilla: str) -> AngulosServo:
        coord = self._sistema_brazo.casilla_a_xyz(casilla)
        if not self._sistema_brazo.es_alcanzable(coord.x, coord.y, coord.z):
            raise ValueError(f"casilla {casilla} fuera de alcance ({coord.x:.1f},{coord.y:.1f})cm")
        angulos = self._sistema_brazo.calcular_angulos(coord.x, coord.y, coord.z)
        return self._sistema_brazo.angulos_a_servos(angulos)

    # ── Turno PC ─────────────────────────────

    def _turno_pc(self):
        with Live(
            Spinner('dots', text=' [white]PC pensando...[/white]'),
            console=console,
            refresh_per_second=10,
        ):
            mov = mejor_movimiento(self.estado, self.profundidad)

        if mov is None:
            return

        pieza_cap = self.estado.tablero[mov.hasta[0]][mov.hasta[1]]
        if pieza_cap:
            self.capturadas_por_pc.append(pieza_cap)

        desde_str = indices_a_casilla(*mov.desde)
        hasta_str = indices_a_casilla(*mov.hasta)
        self.ultimo_mov_pc = f"{desde_str} → {hasta_str}"
        self.ultimo_mov_pc_casillas = {mov.desde, mov.hasta}

        self._emitir_movimiento_brazo(desde_str, hasta_str, autor="PC")

        self.estado = aplicar_movimiento(self.estado, mov)

    # ── Turno jugador ─────────────────────────

    def _turno_jugador(self):
        if es_en_jaque(self.estado, 'B'):
            console.print("  ⚠  [bold red]¡JAQUE! Tu Rey está en peligro[/bold red]")

        while True:
            entrada = console.input(
                "\n  [bold]>[/bold] Jugada [dim](ej: [cyan]E7-E5[/cyan])[/dim] "
                "o casilla para ver opciones [dim]([cyan]E7[/cyan])[/dim] "
                "o [dim][cyan]ayuda[/cyan] / [cyan]salir[/cyan][/dim]: "
            ).strip().upper()

            if entrada in ('SALIR', 'S'):
                raise SystemExit
            if entrada in ('AYUDA', 'A', 'H'):
                self._ayuda()
                continue

            # Jugada completa: "E7-E5" o "E7E5"
            if '-' in entrada and len(entrada) == 5:
                partes = entrada.split('-')
                if len(partes) == 2:
                    orig = casilla_a_indices(partes[0])
                    dest = casilla_a_indices(partes[1])
                    if orig and dest:
                        if self._ejecutar(orig, dest):
                            return
                        continue
            elif len(entrada) == 4:
                orig = casilla_a_indices(entrada[:2])
                dest = casilla_a_indices(entrada[2:])
                if orig and dest:
                    if self._ejecutar(orig, dest):
                        return
                    continue

            # Solo casilla: mostrar opciones
            elif len(entrada) == 2:
                orig = casilla_a_indices(entrada)
                if not orig:
                    console.print("  [red]✗ Casilla inválida[/red]")
                    continue
                f, c = orig
                pieza = self.estado.tablero[f][c]
                if not pieza or pieza.color != 'B':
                    console.print("  [red]✗ No hay una pieza tuya en esa casilla[/red]")
                    continue
                movs_pieza = [m for m in movimientos_legales(self.estado, 'B') if m.desde == orig]
                if not movs_pieza:
                    console.print("  [red]✗ Esa pieza no tiene movimientos válidos[/red]")
                    continue

                dests = {m.hasta for m in movs_pieza}
                console.clear()
                self._dibujar_pantalla(sel=orig, dests=dests)
                nombre = _NOMBRE_PIEZA.get(pieza.tipo, pieza.tipo)
                console.print(
                    f"  [green]✓ {nombre} en {entrada} — "
                    f"{len(movs_pieza)} movimiento(s) posible(s)[/green]"
                )
                dest_str = console.input(
                    "  [bold]>[/bold] Destino [dim](ej: [cyan]E5[/cyan])[/dim] "
                    "o [dim]ENTER para cancelar[/dim]: "
                ).strip().upper()
                if not dest_str:
                    console.clear()
                    self._dibujar_pantalla()
                    continue
                dest = casilla_a_indices(dest_str)
                if not dest:
                    console.print("  [red]✗ Casilla inválida[/red]")
                    continue
                if self._ejecutar(orig, dest):
                    return
                continue
            else:
                console.print("  [red]✗ Formato inválido. Usa E7-E5 o solo E7[/red]")

    def _ejecutar(self, origen: tuple, destino: tuple) -> bool:
        """Valida y ejecuta el movimiento. Retorna True si fue exitoso."""
        legales = movimientos_legales(self.estado, 'B')
        candidatos = [m for m in legales if m.desde == origen and m.hasta == destino]

        if not candidatos:
            console.print("  [red]✗ Movimiento inválido[/red]")
            return False

        mov = candidatos[0]

        # Promoción: preguntar qué pieza
        if mov.promocion:
            pr = console.input(
                "  [bold]Promoción[/bold] — elige: "
                "[cyan]r[/cyan]=Reina  [cyan]T[/cyan]=Torre  "
                "[cyan]A[/cyan]=Alfil  [cyan]C[/cyan]=Caballo: "
            ).strip().lower()
            mapa = {'r': 'r', 't': 'T', 'a': 'A', 'c': 'C'}
            tipo_promo = mapa.get(pr, 'r')
            mov = next((m for m in candidatos if m.promocion == tipo_promo), candidatos[0])

        pieza_cap = self.estado.tablero[destino[0]][destino[1]]
        if pieza_cap:
            self.capturadas_por_ti.append(pieza_cap)

        desde_str = indices_a_casilla(*origen)
        hasta_str = indices_a_casilla(*destino)

        # No movemos el brazo en la jugada del jugador — el jugador mueve la pieza
        # físicamente. El brazo solo trabaja en el turno de la PC.
        self.estado = aplicar_movimiento(self.estado, mov)
        console.print(f"  [green]✓ {desde_str} → {hasta_str}[/green]  [dim](movelo en el tablero físico)[/dim]")
        return True

    # ── Fin de partida ────────────────────────

    def _fin(self, resultado: str):
        console.clear()
        self._dibujar_pantalla()
        color_perdedor = self.estado.turno
        ganador = 'Blancas (PC)' if color_perdedor == 'B' else 'Negras (Tú)'

        textos = {
            'jaque_mate': (
                "★  JAQUE MATE  ★",
                f"Ganan las {ganador}",
            ),
            'ahogado': ("TABLAS", "Ahogado — sin movimientos posibles"),
            'material': ("TABLAS", "Material insuficiente"),
            '50_movimientos': ("TABLAS", "Regla de los 50 movimientos"),
        }
        titulo, subtitulo = textos.get(resultado, ("FIN", ""))
        console.print(Panel(
            Align.center(
                f"[bold yellow]{titulo}[/bold yellow]\n"
                f"{subtitulo}\n"
                f"[dim]Total de jugadas: {self.jugada_num}[/dim]"
            ),
            border_style="yellow",
            padding=(1, 4),
        ))
        console.input("\n  Presiona ENTER para salir...")

    # ── Ayuda ────────────────────────────────

    def _ayuda(self):
        console.print(Panel(
            "[bold]Piezas (letras españolas):[/bold]\n"
            "  [cyan]R[/cyan]=Rey   [cyan]r[/cyan]=Reina  [cyan]T[/cyan]=Torre\n"
            "  [cyan]A[/cyan]=Alfil [cyan]C[/cyan]=Caballo [cyan]P[/cyan]=Peón\n\n"
            "[bold]Colores:[/bold]\n"
            "  [bold bright_white]Blancas = PC[/bold bright_white]   "
            "[bold bright_cyan]Negras = Tú[/bold bright_cyan]\n\n"
            "[bold]Comandos:[/bold]\n"
            "  [cyan]E7-E5[/cyan]  → mover directamente\n"
            "  [cyan]E7[/cyan]     → ver casillas válidas de esa pieza\n"
            "  [cyan]AYUDA[/cyan]  → esta pantalla\n"
            "  [cyan]SALIR[/cyan]  → terminar partida\n\n"
            "[bold]Tablero:[/bold]\n"
            "  [on green4]   [/on green4] Pieza seleccionada\n"
            "  [on dark_goldenrod]   [/on dark_goldenrod] Destino válido\n"
            "  [on red3]   [/on red3] Rey en jaque",
            title="[bold]Ayuda[/bold]",
            border_style="blue",
        ))


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    try:
        JuegoAjedrez().iniciar()
    except KeyboardInterrupt:
        console.print("\n[dim]Partida interrumpida.[/dim]")
    except SystemExit:
        console.print("\n[dim]¡Hasta pronto![/dim]")


if __name__ == '__main__':
    main()
