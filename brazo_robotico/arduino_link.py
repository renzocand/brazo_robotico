"""
Conexión serial con el Arduino que controla el brazo robótico.

Protocolo (texto, terminado en '\n'):
    PC → Arduino:  "base1,brazo1_1,brazo2_1|base2,brazo1_2,brazo2_2"
    Arduino → PC:  "OK"  cuando termina el movimiento
                   "ERR <motivo>" si falló
                   "READY" al arrancar
                   "PONG" en respuesta a "PING"

Uso típico:

    enlace = ArduinoLink(puerto="COM3")
    enlace.conectar()
    enlace.enviar_movimiento(servos_origen, servos_destino)
    enlace.cerrar()
"""

from __future__ import annotations

import time
from typing import Optional

from brazo_robotico.tipos import AngulosServo


class ArduinoLink:
    def __init__(
        self,
        puerto: Optional[str] = None,
        baudios: int = 9600,
        timeout: float = 0.5,
        espera_arranque: float = 2.0,
    ):
        """
        puerto: 'COM3' (Windows), '/dev/ttyACM0' (Linux), '/dev/cu.usbmodemXXXX' (macOS).
                Si es None, hay que llamar a `detectar_puerto()` antes de conectar.
        baudios: tiene que coincidir con `BAUDIOS` del sketch (9600 por defecto).
        timeout: segundos máximos esperando una línea de respuesta.
        espera_arranque: el Arduino se reinicia al abrir el puerto serie; este es
                el tiempo a esperar antes de mandar el primer comando.
        """
        self.puerto = puerto
        self.baudios = baudios
        self.timeout = timeout
        self.espera_arranque = espera_arranque
        self._serial = None  # se setea en conectar()

    # ── Conexión ──────────────────────────────

    def conectar(self) -> None:
        """Abre el puerto serie. Lanza ImportError si pyserial no está instalado."""
        try:
            import serial  # pyserial
        except ImportError as e:
            raise ImportError(
                "pyserial no está instalado. Ejecuta: pip install pyserial"
            ) from e

        if self.puerto is None:
            raise ValueError(
                "No hay puerto configurado. Usá detectar_puerto() o pasá `puerto=`."
            )

        self._serial = serial.Serial(
            port=self.puerto,
            baudrate=self.baudios,
            timeout=self.timeout,
        )
        # El Arduino se reinicia al abrir el puerto (DTR). Esperamos a que arranque.
        time.sleep(self.espera_arranque)
        self._serial.reset_input_buffer()

    def cerrar(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None

    @property
    def conectado(self) -> bool:
        return self._serial is not None and self._serial.is_open

    # ── Envío de comandos ─────────────────────

    def enviar_movimiento(
        self,
        origen: AngulosServo,
        destino: AngulosServo,
        esperar_ok: bool = True,
        timeout_movimiento: float = 30.0,
    ) -> str:
        """
        Manda los ángulos para que el brazo recoja en `origen` y suelte en `destino`.
        Retorna la línea de respuesta del Arduino ("OK" / "ERR ..." / "" si no esperó).
        """
        if not self.conectado:
            raise RuntimeError("Arduino no conectado. Llamá a conectar() primero.")

        linea = self._formatear(origen, destino)
        self._serial.write((linea + "\n").encode("ascii"))
        self._serial.flush()

        if not esperar_ok:
            return ""

        return self._esperar_respuesta(timeout_movimiento)

    def enviar_sin_esperar(self, origen: AngulosServo, destino: AngulosServo) -> None:
        """
        Manda los ángulos sin bloquear esperando OK.
        Usar `leer_respuesta_no_bloqueante()` después en un loop.
        """
        if not self.conectado:
            raise RuntimeError("Arduino no conectado.")
        linea = self._formatear(origen, destino)
        self._serial.write((linea + "\n").encode("ascii"))
        self._serial.flush()

    def leer_respuesta_no_bloqueante(self) -> str:
        """
        Devuelve una línea completa si hay disponible, o cadena vacía si no.
        Filtra mensajes de status (READY) y devuelve solo OK/ERR/PONG/PROG.
        """
        if self._serial is None or not self._serial.is_open:
            return ""
        if self._serial.in_waiting <= 0:
            return ""
        linea = self._serial.readline().decode("ascii", errors="replace").strip()
        return linea

    def home(self, timeout_movimiento: float = 10.0) -> str:
        """Manda el brazo a posición segura (90,90,90)."""
        if not self.conectado:
            raise RuntimeError("Arduino no conectado.")
        self._serial.write(b"HOME\n")
        self._serial.flush()
        return self._esperar_respuesta(timeout_movimiento)

    def ping(self) -> bool:
        """Devuelve True si el Arduino responde PONG en menos de 1 segundo."""
        if not self.conectado:
            return False
        self._serial.reset_input_buffer()
        self._serial.write(b"PING\n")
        self._serial.flush()
        respuesta = self._esperar_respuesta(timeout=1.5)
        return respuesta.strip().upper() == "PONG"

    # ── Utilidades ────────────────────────────

    @staticmethod
    def _formatear(origen: AngulosServo, destino: AngulosServo) -> str:
        return (
            f"{origen.base:.1f},{origen.brazo1:.1f},{origen.brazo2:.1f}|"
            f"{destino.base:.1f},{destino.brazo1:.1f},{destino.brazo2:.1f}"
        )

    def _esperar_respuesta(self, timeout: float) -> str:
        """Lee líneas hasta encontrar OK / ERR, o se acaba el tiempo."""
        if self._serial is None:
            return ""
        inicio = time.time()
        while time.time() - inicio < timeout:
            linea = self._serial.readline().decode("ascii", errors="replace").strip()
            if not linea:
                continue
            if linea.startswith("OK") or linea.startswith("ERR") or linea == "PONG":
                return linea
            # Otras líneas (READY, mensajes de debug) se ignoran
        return ""

    @staticmethod
    def detectar_puerto() -> Optional[str]:
        """
        Busca el primer puerto que parezca un Arduino y devuelve su nombre.
        Devuelve None si no encuentra ninguno.
        """
        try:
            from serial.tools import list_ports
        except ImportError:
            return None

        candidatos = []
        for p in list_ports.comports():
            descripcion = (p.description or "").lower()
            manufacturer = (p.manufacturer or "").lower()
            if (
                "arduino" in descripcion
                or "arduino" in manufacturer
                or "ch340" in descripcion
                or "usb-serial" in descripcion
                or "usb serial" in descripcion
                or "usbmodem" in (p.device or "")
            ):
                candidatos.append(p.device)

        if candidatos:
            return candidatos[0]
        # Fallback: si solo hay un puerto serie, usarlo
        puertos = list(list_ports.comports())
        if len(puertos) == 1:
            return puertos[0].device
        return None
