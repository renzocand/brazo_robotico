# Brazo Robótico

Sistema de control y visualización para un brazo robótico con capacidades de cinemática y movimiento de piezas.

## Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)

## Instalación

### 1. Clonar o descargar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd brazo_robotico
```

### 2. Crear un entorno virtual (recomendado)

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar la aplicación principal

Para iniciar el sistema de control del brazo robótico:

```bash
python main.py
```

### Ejecutar los tests

Para ejecutar todos los tests:

```bash
pytest tests/
```

Para ejecutar tests de un módulo específico:

```bash
pytest tests/test_cinematica.py
pytest tests/test_movimiento.py
pytest tests/test_sistema.py
pytest tests/test_tablero.py
pytest tests/test_visualizacion.py
```

Para ejecutar con más detalle:

```bash
pytest tests/ -v
```

## Estructura del proyecto

```
brazo_robotico/
├── __init__.py              # Inicializador del paquete
├── cinematica.py            # Cálculos de cinemática
├── config.py                # Configuración del sistema
├── mover_pieza.py           # Lógica para mover piezas
├── movimiento.py            # Gestión de movimientos
├── sistema.py               # Sistema principal
├── tablero.py               # Control del tablero
├── tipos.py                 # Tipos y estructuras de datos
└── visualizacion.py         # Visualización gráfica

tests/
├── __init__.py
├── test_cinematica.py       # Tests de cinemática
├── test_movimiento.py       # Tests de movimiento
├── test_sistema.py          # Tests del sistema
├── test_tablero.py          # Tests del tablero
└── test_visualizacion.py    # Tests de visualización

main.py                       # Punto de entrada principal
requirements.txt             # Dependencias del proyecto
README.md                     # Este archivo
```

## Dependencias

- **rich**: Librería para output enriquecido en terminal
- **pytest**: Framework para testing
- **matplotlib**: Librería para visualización gráfica

## Notas

- Asegúrate de tener el entorno virtual activado antes de ejecutar comandos
- Para desactivar el entorno virtual, usa: `deactivate`
