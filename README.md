# Brazo Robótico — Ajedrez contra el brazo

Sistema completo para jugar ajedrez **contra un brazo robótico real**.
La PC piensa la jugada con un algoritmo Alpha-Beta, calcula la cinemática
inversa para los servos del brazo, y le envía los ángulos al Arduino por
USB. El Arduino mueve los servos suavemente, recoge la pieza con la pinza,
la suelta en la casilla destino y vuelve a una posición "plegada" para
liberar el tablero. **Solo se mueve para las jugadas de la PC** — vos movés
tus piezas a mano y le decís al programa qué jugaste.

```
   ┌─────────────────────┐   USB    ┌─────────────────┐    PWM    ┌────────┐
   │  PC (Python)        │ ──────►  │  Arduino Uno    │ ────────► │ Servos │
   │  • Ajedrez α-β      │ Serial   │  • Recibe CSV   │ D3/6/10/11│  4×    │
   │  • Cinemática inv.  │ ◄──────  │  • Mueve servos │           └────────┘
   │  • Animación CLI    │   "OK"   │  • Confirma     │
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
7. [Calibración del brazo (medir L1, L2, H)](#7-calibración-del-brazo-medir-l1-l2-h)
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
- **4 servomotores**: base, hombro, codo y pinza
- **Fuente externa 5V/2A** o **pack de 4 pilas AA** (ver §4)
- Cables jumper macho-macho y macho-hembra
- Protoboard (recomendado, casi obligatorio)
- Capacitor electrolítico 470–1000 µF (recomendado)

> Este proyecto está calibrado para el kit MDF **RIO-ONLINE** (estilo EEZYbotARM con varillas paralelas, 4 micro-servos SG90). Si tu brazo es distinto, las medidas en `config.py` van a cambiar pero el sistema funciona igual.

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

Esto instala: `rich`, `pytest`, `matplotlib`, `PyQt5` y **`pyserial`** (para hablar con el Arduino).

### 2.4 Instalar el Arduino IDE

Descargar de https://www.arduino.cc/en/software y ejecutar el instalador. En la primera ejecución acepta los drivers.

> **Si tu Arduino es clon** (chip CH340 en vez de ATmega16U2): instalá también el driver CH340 desde https://sparks.gogo.co.nz/ch340.html. Si no, Windows no lo va a reconocer.

---

## 3. Hardware: lista de materiales

| Cantidad | Componente | Notas |
|---:|---|---|
| 1 | Arduino Uno | original o clon |
| 1 | Cable USB A-B | "de impresora" |
| 4 | Servomotor SG90 | uno por articulación: base, hombro, codo, pinza |
| 1 | Fuente 5V 2A | o portapilas 4×AA con interruptor (≈6V) |
| 1 | Protoboard | casi obligatorio para repartir alimentación |
| 1 | Capacitor 1000 µF (electrolítico) | suaviza picos de corriente |
| ~10 | Jumpers M-M y M-H | |

> **¿Por qué fuente externa?** El pin 5V del Arduino solo puede entregar ~500 mA. **4 servos en movimiento pueden pedir 2–3 A en picos** y queman el regulador del Arduino. **SIEMPRE fuente externa para los servos.**

---

## 4. Cableado del Arduino

### 4.1 Pines de señal (cable amarillo/naranja de cada servo)

| Servo | Articulación | Pin Arduino |
|---|---|:-:|
| Servo 1 | **Base** (rotación horizontal) | **D3** |
| Servo 2 | **Hombro** / brazo1 (sube y baja) | **D6** |
| Servo 3 | **Codo** / brazo2 / muñeca | **D10** |
| Servo 4 | **Pinza** (0=abre, 60=cierra) | **D11** |

### 4.2 Conexión por servo

Cada servo tiene 3 cables:

| Color cable | Va a |
|---|---|
| **Rojo** (V+) | **+5V de la fuente externa** (NO al 5V del Arduino) |
| **Marrón / negro** (GND) | **GND de la fuente externa** *Y* **GND del Arduino** (común) |
| **Naranja / amarillo** (señal) | Pin digital del Arduino (según tabla anterior) |

### 4.3 Esquema completo

```
                                      ┌──── Servo Base    (V+)  → D3 señal
   Fuente externa +5V ────────────────┼──── Servo Hombro  (V+)  → D6 señal
                                      ├──── Servo Codo    (V+)  → D10 señal
                                      └──── Servo Pinza   (V+)  → D11 señal

                                      ┌──── Servo Base    (GND)
   Fuente externa GND ──────┬─────────┼──── Servo Hombro  (GND)
                            │         ├──── Servo Codo    (GND)
                            │         └──── Servo Pinza   (GND)
                            │
                            └─────────► GND del Arduino   ← ¡CRÍTICO! GND COMÚN

                            Capacitor 1000 µF entre +5V y GND
                            (opcional pero recomendado)
```

> ⚠ **Regla de oro #1:** GND del Arduino, GND de la fuente externa y GND de los servos **deben estar todos unidos**. Sin GND común los servos hacen movimientos erráticos o no se mueven, y se pueden quemar.
>
> ⚠ **Regla de oro #2:** Voltaje 4.8 a 6V. **NO uses 9V ni 12V** o quemás los servos al instante.

### 4.4 Capacitor (recomendado)

Cuando los servos arrancan a moverse, chupan corriente de golpe → la tensión cae → el Arduino se resetea o los servos tiemblan. Un capacitor electrolítico de **470–1000 µF** entre los rieles + y − del protoboard, lo más cerca posible de los servos, amortigua esos picos.

> **Ojo con la polaridad** del capacitor: el cable largo es el +, el corto es el GND.

---

## 5. Cargar el sketch en el Arduino

### 5.1 Abrir el sketch principal

1. Arduino IDE → `Archivo → Abrir...` → elegí:
   ```
   <carpeta del proyecto>/arduino/brazo_robotico/brazo_robotico.ino
   ```

### 5.2 Seleccionar la placa y el puerto

2. `Herramientas → Placa → Arduino AVR Boards → Arduino Uno`
3. Conectá el Arduino al USB
4. `Herramientas → Puerto → COMx` (Windows) o `/dev/ttyACM0` (Linux). **Anotá el COM** que aparece, te hace falta en §6.

### 5.3 Compilar y subir

5. Tocá el botón **flecha (→)** en la barra superior (o `Ctrl+U`)
6. Esperá a que diga `Carga finalizada` abajo

### 5.4 Verificar que arrancó

7. Abrí el **Monitor Serie** (`Herramientas → Monitor Serie` o `Ctrl+Shift+M`)
8. Configurá la velocidad a **9600 baudios** abajo a la derecha
9. Apretá el botón RESET del Arduino → tendría que decir `READY`
10. Tipeá `PING` y enviá → debería responder `PONG`
11. Tipeá `90,90,90|90,90,90` → los servos van a 90° y responde `OK`

> **Importante**: cerrá el Monitor Serie antes de correr Python. **Solo un programa a la vez** puede usar el puerto serie.

---

## 6. Configurar Python para que hable con el Arduino

### 6.1 Editar `brazo_robotico/config.py`

Buscá la sección **CONEXIÓN ARDUINO**:

```python
ARDUINO_PUERTO = "COM4"        # ← reemplazá por el COM de tu Arduino
ARDUINO_BAUDIOS = 9600         # debe coincidir con BAUDIOS del sketch
ARDUINO_HABILITADO = True      # True = enviar al brazo real
```

> Si dejás `ARDUINO_PUERTO = None` y `ARDUINO_HABILITADO = True`, el programa intenta detectar el puerto automáticamente.

### 6.2 Probar la conexión

Con el Arduino conectado y el Monitor Serie del IDE **cerrado**:

```bash
python -c "from brazo_robotico.arduino_link import ArduinoLink; \
l = ArduinoLink('COM4'); l.conectar(); print('PING:', l.ping()); l.cerrar()"
```

Tendría que imprimir `PING: True`. Si dice `False` o tira error → ver §10.

---

## 7. Calibración del brazo (medir L1, L2, H)

El cálculo de cinemática necesita las **medidas físicas reales** de tu brazo. Con valores incorrectos, **muchas casillas distintas terminan dando los mismos ángulos** → el brazo no se mueve a la posición correcta.

### 7.1 Subir el sketch de calibración

Hay un sketch separado que **estira el brazo a 170°** para que puedas medir cómodo:

1. En el IDE de Arduino, `Archivo → Abrir...`:
   ```
   arduino/brazo_robotico/calibracion_servo/calibracion_servo.ino
   ```
2. Subilo (botón →)
3. El brazo se va a estirar suavemente

### 7.2 Medir con regla

Con el brazo extendido y la pinza cerrada:

```
     ●  punta de la pinza cerrada
     │
     │ L2 = del eje de la MUÑECA (codo) a la PUNTA DE LA PINZA
     │
     ●  eje de la muñeca / codo (servo)
     │
     │ L1 = del eje del HOMBRO al eje de la MUÑECA
     │
     ●  eje del hombro (servo)
     │
     │ H = del eje del HOMBRO al PLANO del tablero
     │
   ──┴── tablero
```

| Medida | Qué es | Ejemplo |
|---|---|---|
| **L1** | del eje del hombro al eje del codo | 15 cm |
| **L2** | del eje del codo a la punta de la pinza cerrada | 15.9 cm |
| **H** | altura del eje del hombro al plano del tablero | (a medir según tu mesa) |
| **OFFSET** | de la base del brazo al borde más cercano del tablero | 5 cm |

### 7.3 Cargar las medidas en `config.py`

```python
LARGO_PRIMER_BRAZO = 15.0      # tu L1 medido
LARGO_SEGUNDO_BRAZO = 15.9     # tu L2 medido
OFFSET_BRAZO = 5.0             # distancia base → tablero
DIAMETRO_CASILLA = 2.5         # lado de cada casilla (en cm)
```

### 7.4 Verificar alcance

Para que las 64 casillas estén alcanzables tiene que cumplirse:

```
L1 + L2  ≥  √(OFFSET² + (8 × DIAMETRO_CASILLA)²)
```

Ejemplo con los valores actuales:
- Alcance del brazo: 15 + 15.9 = 30.9 cm
- Distancia a casilla más lejana: √(5² + 20²) ≈ 20.6 cm ✓

### 7.5 Volver al sketch principal

Cuando termines de medir, **volvé a subir** `arduino/brazo_robotico/brazo_robotico.ino` (no el de calibración) para usar el juego.

### 7.6 Calibrar la dirección de los servos (si es necesario)

Si al jugar ves que el brazo va al **lado opuesto**, en `config.py`:

```python
SERVO_BASE_SIGNO = 1.0     # poné -1.0 si la base gira al revés
SERVO_BRAZO1_SIGNO = 1.0   # poné -1.0 si el hombro sube cuando debería bajar
SERVO_BRAZO2_SIGNO = 1.0   # idem para el codo
```

Y los `OFFSET` ajustan dónde queda el "centro" de cada servo (típicamente 90° = posición media).

---

## 8. Cómo se juega

### 8.1 Arrancar el juego

```bash
python main.py
```

### 8.2 Flujo de una partida

1. **Pantalla de bienvenida** — elegí dificultad:
   - `1` Fácil (PC ve 2 jugadas adelante)
   - `2` Intermedio (PC ve 3 jugadas)
   - `3` Difícil (PC ve 4 jugadas)
2. **Conexión Arduino** — ves `✓ Arduino conectado en COMx` si todo está bien.
3. **Las Blancas (PC) abren** — la PC piensa, calcula los ángulos, **el brazo agarra la pieza física, la mueve y la suelta**, vuelve a parked.
4. **Tu turno (Negras)** — vos movés tu pieza FÍSICAMENTE en el tablero, y luego tipeás qué jugaste:
   - `E7-E5` → mover directo
   - `E7` → solo la casilla → te muestra todas las jugadas legales de esa pieza
   - `AYUDA` → pantalla de ayuda
   - `SALIR` → terminar
5. **El brazo solo se mueve cuando juega la PC**, no cuando jugás vos. Tu jugada se registra y listo.
6. **Animación en vivo** durante cada jugada de la PC:

```
  Brazo robótico — PC: E2 → E4
  → Arduino: 95.3,142.5,128.1|92.1,156.8,143.7
┌────────────────────────────┬────────────┬───────────────┬───────────────┬───────────────┐
│ Fase                       │ Servo Base │ Servo Brazo 1 │ Servo Brazo 2 │     Pinza     │
├────────────────────────────┼────────────┼───────────────┼───────────────┼───────────────┤
│ ████░░░░░░ Yendo a recoger │      94.5° │        128.3° │        110.2° │   abierta     │
└────────────────────────────┴────────────┴───────────────┴───────────────┴───────────────┘
```

Las fases que vas a ver:
1. **Yendo a recoger** (parked → casilla origen)
2. **Agarrando pieza** (cierra pinza, pausa)
3. **Yendo a soltar** (origen → destino)
4. **Soltando pieza** (abre pinza, pausa)
5. **Volviendo a parked** (libera el tablero)
6. **Completado** ✓

### 8.3 La posición "parked"

Después de cada jugada, el brazo vuelve a **(base=90°, hombro=90°, codo=90°, pinza=cerrada)**. Esto deja el tablero libre para que vos puedas mover tu pieza tranquilo.

Para cambiar la posición parked, editá las constantes `PARKED_*` al principio del sketch [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino) y resubí.

> ⚠ **Nunca pongas PARKED en 0° o 180°** — son los topes mecánicos. Si la articulación no llega exactamente, el servo se queda forzando contra el tope y **se quema** en minutos.

### 8.4 Reglas de ajedrez implementadas

- ✅ Movimientos básicos de todas las piezas
- ✅ Enroque corto y largo (con validación de jaque)
- ✅ Captura al paso (en passant)
- ✅ Promoción de peón
- ✅ Detección de jaque, jaque mate y ahogado
- ✅ Regla de los 50 movimientos
- ✅ Material insuficiente

---

## 9. Modo simulación (sin Arduino)

Si todavía no terminaste de armar el brazo, o querés probar el algoritmo sin el hardware:

En `brazo_robotico/config.py`:
```python
ARDUINO_HABILITADO = False
```

El juego corre normal y muestra la animación en pantalla, pero no manda nada al puerto serie. Útil para:
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

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Acceso denegado" al subir el sketch desde el IDE

El puerto COM está ocupado por otro programa. Cerrá:
- El Monitor Serie del IDE
- Cualquier `python main.py` corriendo
- Otras instancias del IDE

Si nada funciona, desconectá y reconectá el USB.

### Arduino no aparece como puerto

- ¿Cable USB con datos? (algunos USB son solo de carga)
- Probá otro puerto USB
- Si es **clon**: instalá driver CH340 (https://sparks.gogo.co.nz/ch340.html)
- Reiniciá la PC tras instalar el driver

### "Modo simulación" cuando esperabas el Arduino conectado

1. Verificá que `ARDUINO_HABILITADO = True` en `config.py`
2. Verificá que `ARDUINO_PUERTO` tenga el COM correcto (o sea `None` para autodetección)
3. Cerrá el Monitor Serie del IDE
4. Probá `python -c "from brazo_robotico.arduino_link import ArduinoLink; print(ArduinoLink.detectar_puerto())"`

### Servo se quema (humo, olor a plástico)

**Causas más comunes** (por orden de frecuencia):

1. **GND no común** entre Arduino y fuente externa → señal PWM errática → servo stallea
2. **Servo en posición de tope mecánico** (PARKED en 0° o 180°) → motor forzando continuamente
3. **Voltaje muy alto** (>6V) → quema instantánea
4. **Alimentado desde el 5V del Arduino** → sobrecarga el regulador

Antes de conectar el reemplazo, **revisá las 4 causas**. Las reglas:
- 🚫 Nunca alimentar servos desde el 5V del Arduino
- 🚫 Nunca voltaje >6V
- 🚫 Nunca PARKED en 0° o 180° sin verificar tope físico
- ✅ Siempre GND común entre fuente externa y Arduino
- ✅ Si oís un servo zumbando o lo sentís caliente, **desconectá YA**

### Servos vibran, tartamudean o se mueven raro

Casi siempre alimentación o GND:
- ¿GND de la fuente externa unido al GND del Arduino?
- ¿Pilas viejas? Cambialas o usá fuente de pared
- ¿La fuente da suficiente corriente? (mínimo 2A para 4 servos)
- ¿Tenés capacitor cerca de los servos?

### `ERR angulo fuera de rango`

El cálculo dio un ángulo fuera del rango permitido (10–170° por defecto). Causas:
- `SERVO_*_OFFSET` mal calibrado
- `SERVO_*_SIGNO` invertido (pieza en el lado opuesto)
- Casilla muy lejos del brazo (revisá `OFFSET_BRAZO` y las medidas L1/L2)

### El brazo se mueve, pero todas las casillas dan los mismos ángulos

Probablemente las **medidas L1/L2/OFFSET están mal** (no son las de tu brazo real). El cálculo da ángulos fuera de rango, se clampean al límite y muchas casillas distintas terminan con los mismos ángulos clampeados.

**Solución**: usar el sketch de calibración (`calibracion_servo.ino`) para estirar el brazo y medir con regla. Ver §7.

### El brazo se mueve muy rápido / muy lento

En el sketch [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino), ajustá:

```cpp
#define MS_POR_PASO 120     // ms entre cada grado de movimiento
                            // Más alto = más lento y suave
                            // 60 = rápido, 120 = actual, 200 = muy lento
#define PAUSA_AGARRE 2000   // ms de pausa cuando agarra/suelta
                            // Más alto = pinza tiene más tiempo
```

Después de cambiar, **también actualizá** `config.py` con los mismos valores en `ARDUINO_MS_POR_PASO` y `ARDUINO_PAUSA_AGARRE_MS` para que la animación de Python siga sincronizada. Y **resubí el sketch**.

### Casilla "fuera de alcance"

El brazo no llega físicamente. Comprobá:

```
L1 + L2  ≥  √(OFFSET² + (8 × DIAMETRO_CASILLA)²)
```

Si no se cumple, opciones:
- Tablero con casillas más chicas (ajustar `DIAMETRO_CASILLA`)
- Tablero más cerca de la base (bajar `OFFSET_BRAZO`)
- Tablero más chico físicamente (no usar las filas/columnas más lejanas)

---

## 11. Estructura del proyecto

```
brazo_robotico/
│
├── main.py                          ← punto de entrada
├── requirements.txt                 ← dependencias Python
├── README.md                        ← este archivo
├── test_arduino.py                  ← script de diagnóstico de conexión
├── test_angulos.py                  ← muestra ángulos calculados por casilla
│
├── brazo_robotico/                  ← módulo principal
│   ├── ajedrez.py                   ← motor de ajedrez (Alpha-Beta + UI + animación)
│   ├── arduino_link.py              ← comunicación serial con Arduino
│   ├── cinematica.py                ← cinemática inversa
│   ├── config.py                    ← TODA la configuración de Python
│   ├── movimiento.py                ← secuencia de ángulos para mover una pieza
│   ├── mover_pieza.py               ← script viejo, demo individual
│   ├── sistema.py                   ← integra cinemática + tablero + servos
│   ├── tablero.py                   ← geometría del tablero
│   ├── tipos.py                     ← Coordenada, Angulos, AngulosServo
│   └── visualizacion.py             ← gráficos 2D/3D con matplotlib (no usado en juego)
│
├── arduino/
│   └── brazo_robotico/
│       ├── brazo_robotico.ino       ← sketch principal (usar cuando jugás)
│       └── calibracion_servo/
│           └── calibracion_servo.ino  ← sketch para estirar el brazo y medir
│
└── tests/                           ← pytest
    ├── test_cinematica.py
    ├── test_movimiento.py
    ├── test_sistema.py
    ├── test_tablero.py
    └── test_visualizacion.py
```

### Archivos clave por tarea

| Querés... | Editá... |
|---|---|
| Cambiar pines del Arduino | [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino) (`PIN_BASE`, `PIN_BRAZO1`, etc.) |
| Cambiar la posición parked | [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino) (`PARKED_BASE`, etc.) |
| Cambiar velocidad del brazo | [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino) (`MS_POR_PASO`) Y `config.py` (`ARDUINO_MS_POR_PASO`) |
| Cambiar pausa de agarre | [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino) (`PAUSA_AGARRE`) Y `config.py` (`ARDUINO_PAUSA_AGARRE_MS`) |
| Cambiar valores de la pinza | [brazo_robotico.ino](arduino/brazo_robotico/brazo_robotico.ino) Y `config.py` (`PINZA_ABIERTA`, `PINZA_CERRADA`) |
| Cambiar medidas físicas (L1, L2, OFFSET) | [config.py](brazo_robotico/config.py) |
| Cambiar tamaño del tablero | [config.py](brazo_robotico/config.py) (`DIAMETRO_CASILLA`) |
| Calibrar dirección de servos | [config.py](brazo_robotico/config.py) (`SERVO_*_SIGNO` y `SERVO_*_OFFSET`) |
| Configurar puerto COM | [config.py](brazo_robotico/config.py) (`ARDUINO_PUERTO`) |

### Tests

```bash
pytest tests/             # todos
pytest tests/ -v          # con detalle
pytest tests/test_cinematica.py
```

---

## Comandos especiales del Arduino (debug desde el Monitor Serie)

| Comando | Qué hace |
|---|---|
| `PING` | Responde `PONG` |
| `HOME` o `PARK` | Manda los servos a la posición parked |
| `B,B1,B2\|B,B1,B2` | Movimiento real — `B` base, `B1` brazo1 (hombro), `B2` brazo2 (codo) |
| `90,90,90\|90,90,90` | Test: ir y volver a la misma posición central |

Recordá: hay que cerrar el Monitor Serie antes de correr `python main.py`.

---

## Importante: hay parámetros duplicados entre el sketch y `config.py`

Algunos valores tienen que estar **en ambos archivos** porque el Arduino y Python son programas distintos en máquinas distintas:

| Parámetro | En el sketch (.ino) | En `config.py` |
|---|---|---|
| Velocidad del brazo | `MS_POR_PASO` | `ARDUINO_MS_POR_PASO` |
| Pausa de agarre | `PAUSA_AGARRE` | `ARDUINO_PAUSA_AGARRE_MS` |
| Posición parked | `PARKED_BASE/BRAZO1/BRAZO2` | `ARDUINO_PARKED_BASE/BRAZO1/BRAZO2` |
| Valores de pinza | `PINZA_ABIERTA/CERRADA` | `PINZA_ABIERTA/CERRADA` |

Cuando cambiás uno, **acordate de cambiar el otro** o la animación de Python no va a estar sincronizada con el movimiento real.

---

## Licencia / Créditos

Proyecto académico. El motor de ajedrez (Alpha-Beta + Quiescence Search + Piece-Square Tables) está inspirado en el estilo de los motores clásicos tipo Chessmaster (Game Boy, 1989).

El kit del brazo es **RIO-ONLINE** (estilo EEZYbotARM, MDF cortado a láser, 4 servos SG90).
