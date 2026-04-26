# Brazo Robótico — Ajedrez contra el brazo

Sistema completo para jugar ajedrez **contra un brazo robótico real**.
La PC piensa la jugada con un algoritmo Alpha-Beta, calcula la cinemática
inversa para los servos del brazo, y le envía los ángulos al Arduino por
USB. El Arduino mueve los servos suavemente para recoger y soltar la pieza.

```
   ┌─────────────────────┐   USB    ┌─────────────────┐    PWM    ┌────────┐
   │  PC (Python)        │ ──────►  │  Arduino Uno    │ ────────► │ Servos │
   │  • Ajedrez α-β      │ Serial   │  • Recibe CSV   │  D9/10/11 │  3×    │
   │  • Cinemática inv.  │ ◄──────  │  • Mueve servos │           └────────┘
   │  • Ángulos servo    │   "OK"   │  • Confirma     │
   └─────────────────────┘          └─────────────────┘
```

---

## Tabla de contenidos

1. [Requisitos](#1-requisitos)
2. [Instalación del software](#2-instalación-del-software)
3. [Hardware: lista de materiales](#3-hardware-lista-de-materiales)
4. [Cableado del Arduino](#4-cableado-del-arduino)
5. [Cargar el sketch en el Arduino](#5-cargar-el-sketch-en-el-arduino)
6. [Configurar Python para que hable con el Arduino](#6-configurar-python-para-que-hable-con-el-arduino)
7. [Calibración del brazo](#7-calibración-del-brazo)
8. [Cómo se juega](#8-cómo-se-juega)
9. [Modo simulación (sin Arduino)](#9-modo-simulación-sin-arduino)
10. [Solución de problemas](#10-solución-de-problemas)
11. [Estructura del proyecto](#11-estructura-del-proyecto)

---

## 1. Requisitos

### Software
- **Python 3.10+** (probado en 3.13)
- **Arduino IDE 2.x** — https://www.arduino.cc/en/software
- **Git** (opcional)

### Hardware
- **Arduino Uno** (original o clon)
- **Cable USB tipo A↔B** (el cable "de impresora")
- **3 servomotores** (uno por articulación: base, brazo 1, brazo 2)
- **Fuente externa 5V/2A** o **pack de 4 pilas AA** (para alimentar los servos)
- Cables jumper macho-macho y macho-hembra
- Protoboard (recomendado)

---

## 2. Instalación del software

### 2.1 Clonar el proyecto

```bash
git clone <URL_DEL_REPOSITORIO>
cd brazo_robotico
```

### 2.2 Crear el entorno virtual de Python

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Instalar las dependencias

```bash
pip install -r requirements.txt
```

Esto instala: `rich`, `pytest`, `matplotlib`, `PyQt5` y **`pyserial`** (que es lo que usa Python para hablarle al Arduino).

### 2.4 Instalar el Arduino IDE

Descargar el instalador de https://www.arduino.cc/en/software y ejecutarlo. En la primera ejecución acepta cuando te pida instalar drivers.

> **Si tu Arduino es clon** (chip CH340 en vez de ATmega16U2): también instalá el driver CH340 desde https://sparks.gogo.co.nz/ch340.html. Si no, Windows no lo va a reconocer.

---

## 3. Hardware: lista de materiales

| Cantidad | Componente | Notas |
|---:|---|---|
| 1 | Arduino Uno | original o clon |
| 1 | Cable USB A-B | cable "de impresora" |
| 3 | Servomotor | SG90 (chico, ~1.8 kg·cm) o MG996R (más fuerte, ~10 kg·cm) |
| 1 | Fuente 5V 2A | o portapilas 4×AA con interruptor |
| 1 | Protoboard | opcional pero recomendado |
| ~10 | Jumpers M-M y M-H | |
| 1 | (opcional) Servo extra | para una pinza/garra |

> **¿Por qué fuente externa?** El pin 5V del Arduino solo puede entregar ~500 mA. Tres servos en movimiento pueden pedir 1.5–3 A pico y queman el regulador del Arduino. **Siempre fuente externa para los servos.**

---

## 4. Cableado del Arduino

### 4.1 Conexión por servo

Cada servo tiene 3 cables:

| Color cable | Va a |
|---|---|
| **Rojo** (V+) | **+5V de la fuente externa** (NO al 5V del Arduino) |
| **Marrón / Negro** (GND) | **GND de la fuente externa** *y* **GND del Arduino** (común) |
| **Naranja / Amarillo** (señal) | Pin digital PWM del Arduino |

### 4.2 Pines de señal por defecto

| Articulación | Pin Arduino |
|---|---|
| Servo Base | **D9** |
| Servo Brazo 1 (hombro) | **D10** |
| Servo Brazo 2 (codo) | **D11** |
| (Opcional) Pinza | D6 |

### 4.3 Esquema simplificado

```
    Fuente 5V externa
       +    -
       │    │
       │    └────────────┬─────────────────┐
       │                 │                 │
       │             [GND Arduino]    [GND fuente]   ← MISMO GND
       │
       ├──[V+ Servo Base]──┐
       ├──[V+ Servo Brazo1]┤   los V+ de los 3 servos van a la fuente
       └──[V+ Servo Brazo2]┘

    Arduino Uno
    ─ D9  ──► señal Servo Base
    ─ D10 ──► señal Servo Brazo 1
    ─ D11 ──► señal Servo Brazo 2
    ─ GND ──► GND fuente externa  (¡crítico!)
    ─ USB ──► PC
```

> **Regla de oro:** GND del Arduino, GND de la fuente externa y GND de los servos **deben estar todos unidos**. Si no, los servos hacen movimientos erráticos o no se mueven.

---

## 5. Cargar el sketch en el Arduino

### 5.1 Abrir el sketch

1. Abrí el **Arduino IDE**
2. `Archivo → Abrir...` y elegí:
   ```
   <carpeta del proyecto>/arduino/brazo_robotico/brazo_robotico.ino
   ```

### 5.2 Seleccionar la placa y el puerto

3. `Herramientas → Placa → Arduino AVR Boards → Arduino Uno`
4. Conectá el Arduino al USB
5. `Herramientas → Puerto → COMx` (Windows) o `/dev/ttyACM0` (Linux). **Anotá ese nombre**, te hace falta más adelante.

### 5.3 Compilar y subir

6. Tocá el botón **→ (Subir)** (o `Ctrl+U`).
7. Esperá a que diga "Carga finalizada" abajo.

### 5.4 Verificar que arrancó

8. Abrí el **Monitor Serie** (`Herramientas → Monitor Serie` o `Ctrl+Shift+M`)
9. Configurá la velocidad a **9600 baudios** abajo a la derecha
10. Presioná el botón de RESET del Arduino: deberías ver `READY`
11. Escribí en la barra de arriba: `PING` y enviá → debería responder `PONG`
12. Escribí: `90,90,90|90,90,90` → los servos van a 90° y luego responde `OK`

> Si el monitor serie está abierto, **el Python no va a poder usar el puerto** (solo un programa a la vez). Cerralo antes de ejecutar el juego.

---

## 6. Configurar Python para que hable con el Arduino

### 6.1 Editar `brazo_robotico/config.py`

Buscá la sección **CONEXIÓN ARDUINO** y cambiá:

```python
ARDUINO_PUERTO = "COM3"        # ← reemplazá por el puerto real de tu Arduino
ARDUINO_BAUDIOS = 9600         # debe coincidir con BAUDIOS del sketch
ARDUINO_HABILITADO = True      # ← cambiá a True para enviar al brazo real
```

> **Tip:** Si dejás `ARDUINO_PUERTO = None` y `ARDUINO_HABILITADO = True`, el programa intenta detectar el puerto automáticamente.

### 6.2 Probar la conexión rápida

Con el Arduino conectado y el monitor serie del IDE **cerrado**:

```bash
python -c "from brazo_robotico.arduino_link import ArduinoLink; \
l = ArduinoLink('COM3'); l.conectar(); print('PING:', l.ping()); l.cerrar()"
```

Debería imprimir `PING: True`. Si dice `False` o tira error → ver [§10](#10-solución-de-problemas).

---

## 7. Calibración del brazo

Las medidas y offsets viven en `brazo_robotico/config.py`. Tenés que ajustarlos a **tu** brazo real:

```python
# Tamaño físico
DIAMETRO_CASILLA = 3.0          # cm — lado de cada cuadro del tablero
LARGO_PRIMER_BRAZO = 23.0       # cm — del hombro al codo
LARGO_SEGUNDO_BRAZO = 19.0      # cm — del codo a la punta
OFFSET_BRAZO = 10.0             # cm — base del brazo al borde más cercano del tablero

# Conversión ángulo matemático → ángulo real del servo
# (ajustar según cómo esté montado cada servo en tu brazo)
SERVO_BASE_OFFSET = 0.0;    SERVO_BASE_SIGNO = 1.0
SERVO_BRAZO1_OFFSET = 90.0; SERVO_BRAZO1_SIGNO = 1.0
SERVO_BRAZO2_OFFSET = 0.0;  SERVO_BRAZO2_SIGNO = 1.0
```

### Procedimiento sugerido

1. Con el brazo armado y los servos atornillados en posición media (~90°), corré:
   ```bash
   python main.py
   ```
2. Hacé un movimiento con piezas en casillas conocidas (ej. `D2-D4`).
3. Mirá la tabla "Brazo robótico" que muestra el programa: te dice los servos para cada paso.
4. Si el brazo apunta al lado equivocado, **invertí el `SIGNO`** (poné `-1.0`).
5. Si está corrido en una articulación, ajustá el `OFFSET` correspondiente.
6. Si una casilla del tablero da "fuera de alcance": revisá `LARGO_PRIMER_BRAZO + LARGO_SEGUNDO_BRAZO ≥ OFFSET_BRAZO + alto_tablero`.

---

## 8. Cómo se juega

```bash
python main.py
```

### Flujo de una partida

1. **Pantalla de bienvenida** — elegí dificultad:
   - `1` Fácil (PC ve 2 jugadas)
   - `2` Intermedio (PC ve 3 jugadas)
   - `3` Difícil (PC ve 4 jugadas)
2. **Conexión Arduino** — si está habilitado, ves `✓ Arduino conectado en COMx`. Si falla, sigue en modo simulación.
3. **Las Blancas (PC) abren** — la PC piensa, mueve la pieza física, espera confirmación del Arduino, te muestra qué jugó.
4. **Tu turno (Negras)** — tipeá tu jugada:
   - `E7-E5` → mover directo
   - `E7` → solo la casilla → te muestra todas las jugadas legales de esa pieza
   - `AYUDA` → pantalla de ayuda
   - `SALIR` → terminar
5. **Cada movimiento muestra:**
   ```
           Brazo robótico — PC: E2 → E4
   ┌─────────┬─────────┬─────────────┬──────────────┬──────────────┐
   │  Paso   │ Casilla │ Servo Base  │ Servo Brazo 1│ Servo Brazo 2│
   ├─────────┼─────────┼─────────────┼──────────────┼──────────────┤
   │ Recoger │   E2    │       93.4° │       112.5° │        48.2° │
   │ Soltar  │   E4    │       92.1° │       101.8° │        62.7° │
   └─────────┴─────────┴─────────────┴──────────────┴──────────────┘
     → Arduino: 93.4,112.5,48.2|92.1,101.8,62.7
     ⠋ Brazo en movimiento...
     ✓ Brazo: movimiento completado
   ```
6. **Fin de partida** — jaque mate, ahogado, regla de 50 movimientos o material insuficiente.

### Reglas implementadas

✅ Movimientos básicos de todas las piezas
✅ Enroque corto y largo (con validación de jaque)
✅ Captura al paso (en passant)
✅ Promoción de peón
✅ Detección de jaque, jaque mate y ahogado
✅ Regla de los 50 movimientos
✅ Material insuficiente

---

## 9. Modo simulación (sin Arduino)

Si todavía no terminaste de armar el brazo o querés probar el algoritmo sin conectar nada:

En `brazo_robotico/config.py`:
```python
ARDUINO_HABILITADO = False
```

El juego corre normal y muestra todos los ángulos por pantalla, pero no manda nada al puerto serie. Útil para:
- Probar la lógica del juego
- Ver qué ángulos saldrían antes de tener el hardware
- Calibrar los offsets en una hoja de cálculo

---

## 10. Solución de problemas

### "Python no se reconoce como comando" (Windows)

El alias de la Microsoft Store está interceptando `python`. Soluciones:
1. **Configuración → Aplicaciones → Configuración avanzada → Alias de ejecución de aplicaciones** → apagá `python.exe` y `python3.exe`
2. O usá `py` en lugar de `python` en todos los comandos

### `venv\Scripts\activate : la ejecución de scripts está deshabilitada`

Permitir scripts firmados localmente para tu usuario:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Arduino no aparece como puerto

- ¿Cable USB con datos? (algunos USB son solo de carga)
- Probá otro puerto USB
- Si es **clon**: instalá driver CH340 (https://sparks.gogo.co.nz/ch340.html)
- Reiniciá la PC tras instalar el driver

### "Modo simulación" cuando esperabas el Arduino conectado

1. Verificá que `ARDUINO_HABILITADO = True` en `config.py`
2. Verificá que `ARDUINO_PUERTO` tenga el puerto correcto (o sea `None` para autodetección)
3. Cerrá el **Monitor Serie del IDE** — el puerto solo lo puede usar un programa a la vez
4. Probá `python -c "from brazo_robotico.arduino_link import ArduinoLink; print(ArduinoLink.detectar_puerto())"`

### `ERR angulo fuera de rango`

El cálculo dio un ángulo fuera de 0–180°. Causas comunes:
- `SERVO_*_OFFSET` mal calibrado
- `SERVO_*_SIGNO` invertido (pieza en el lado opuesto)
- Casilla muy lejos del brazo (revisá `OFFSET_BRAZO`)

### Servos vibran o "tartamudean"

Casi siempre es problema de alimentación:
- ¿Estás alimentando los servos desde el 5V del Arduino? **No lo hagas** — usá fuente externa.
- ¿GND de la fuente externa unido al GND del Arduino? Tiene que estarlo.
- Pilas viejas → cambiarlas o usar fuente de pared.

### El brazo se mueve muy rápido / muy lento

En el sketch, ajustá:
```cpp
#define MS_POR_PASO 15   // ← más alto = más lento y suave (probá 20-30)
```
Recompilá y subí.

### Casilla "fuera de alcance"

Revisá las medidas físicas en `config.py`. Para que todas las 64 casillas estén alcanzables:
```
LARGO_PRIMER_BRAZO + LARGO_SEGUNDO_BRAZO  ≥  OFFSET_BRAZO + (8 × DIAMETRO_CASILLA)
```

---

## 11. Estructura del proyecto

```
brazo_robotico/
│
├── main.py                          ← punto de entrada
├── requirements.txt                 ← dependencias Python
├── README.md                        ← este archivo
│
├── brazo_robotico/                  ← módulo principal
│   ├── ajedrez.py                   ← motor de ajedrez (Alpha-Beta + UI)
│   ├── arduino_link.py              ← comunicación serial con Arduino
│   ├── cinematica.py                ← cinemática inversa
│   ├── config.py                    ← TODA la configuración (ajustá esto)
│   ├── movimiento.py                ← secuencia de ángulos para mover una pieza
│   ├── mover_pieza.py               ← script viejo, demo individual
│   ├── sistema.py                   ← integra cinemática + tablero + servos
│   ├── tablero.py                   ← geometría del tablero
│   ├── tipos.py                     ← Coordenada, Angulos, AngulosServo
│   └── visualizacion.py             ← gráficos 2D/3D con matplotlib
│
├── arduino/
│   └── brazo_robotico/
│       └── brazo_robotico.ino       ← sketch que se sube al Arduino
│
└── tests/                           ← pytest
    ├── test_cinematica.py
    ├── test_movimiento.py
    ├── test_sistema.py
    ├── test_tablero.py
    └── test_visualizacion.py
```

### Archivos clave por tarea

- **Ajustar tamaño/medidas del brazo** → `brazo_robotico/config.py`
- **Calibrar servos** → `brazo_robotico/config.py` (offsets/signos) o el sketch (`PIN_*`)
- **Cambiar pines del Arduino** → `arduino/brazo_robotico/brazo_robotico.ino` (`PIN_BASE`, `PIN_BRAZO1`, `PIN_BRAZO2`)
- **Cambiar velocidad del brazo** → sketch, `MS_POR_PASO`
- **Cambiar dificultad de la IA** → al iniciar el programa, o `DIFICULTAD` en `ajedrez.py`

### Tests

```bash
pytest tests/             # todos
pytest tests/ -v          # con detalle
pytest tests/test_cinematica.py
```

---

## Comandos especiales del Arduino (para debug)

Podés mandarlos desde el Monitor Serie del IDE (a 9600 baudios):

| Comando | Qué hace |
|---|---|
| `PING` | Responde `PONG` |
| `HOME` | Manda los servos a 90,90,90 (posición segura) |
| `90,90,90\|90,90,90` | Movimiento normal — recoger y soltar en la misma posición |
| `B,B1,B2\|B,B1,B2` | Movimiento real — `B` base, `B1` brazo1, `B2` brazo2 |

---

## Licencia / Créditos

Proyecto académico. Las piezas-cuadrado (PSTs), el Alpha-Beta y el Quiescence Search del motor están inspirados en el estilo de los motores de ajedrez clásicos tipo Chessmaster (Game Boy, 1989).
