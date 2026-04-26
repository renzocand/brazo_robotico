// brazo_robotico.ino
// Recibe ángulos de servos por puerto serie y mueve el brazo.
//
// Protocolo:
//   PC envía:  "base1,brazo1_1,brazo2_1|base2,brazo1_2,brazo2_2\n"
//              (ángulos para "recoger" y "soltar", separados por '|')
//   Arduino responde:
//              "OK\n"  cuando terminó el movimiento
//              "ERR <motivo>\n"  si falló el parseo o un ángulo está fuera de rango
//
// Cableado del kit (basado en Brazo_Robot_manual.ino):
//   - Servo Base   (rotación)  -> D3
//   - Servo Brazo1 (hombro)    -> D6
//   - Servo Brazo2 (codo)      -> D10
//   - Pinza        (gripper)   -> D11
//
//   Alimentar los servos con fuente externa (NO desde el 5V del Arduino).
//   GND de la fuente externa DEBE estar unido al GND del Arduino.

#include <Servo.h>

// ──────────────────────────────────────────────
// CONFIGURACIÓN
// ──────────────────────────────────────────────

#define PIN_BASE    3
#define PIN_BRAZO1  6 //brazo que sube y baja
#define PIN_BRAZO2  10 //muñeca

// Pinza/garra en D11. Comentar la siguiente línea si NO tenés pinza.
#define USAR_PINZA
#define PIN_PINZA   11
#define PINZA_ABIERTA 0    // ° pinza abierta
#define PINZA_CERRADA 60   // ° pinza cerrada

// ──────────────────────────────────────────────
// POSICIÓN "PARKED" (el brazo vuelve aquí al inicio y al terminar cada jugada).
// IMPORTANTE: NO usar 0 ni 180 — son los topes mecánicos. Si la articulación
// no puede llegar exactamente, el servo se queda forzando contra el tope y
// se quema. Usar valores intermedios (10°+ alejados de los extremos).
// ──────────────────────────────────────────────
#define PARKED_BASE    90    // base centrada (NUNCA 0 ni 180 sin verificar tope)
#define PARKED_BRAZO1  90    // codo a media altura
#define PARKED_BRAZO2  90    // muñeca centrada
#define PARKED_PINZA   60    // pinza cerrada

// Límites de seguridad por servo. Margen de 10° de cada extremo para
// evitar que el servo se quede forzando contra topes mecánicos.
// Cualquier ángulo fuera de estos rangos se devuelve como ERR.
#define BASE_MIN    10
#define BASE_MAX    170
#define BRAZO1_MIN  10
#define BRAZO1_MAX  170
#define BRAZO2_MIN  10
#define BRAZO2_MAX  170

// Velocidad: ms entre cada paso de 1° (mayor = más lento, más suave)
//   15  = rápido (default original)
//   25  = medio
//   60  = lento y suave
//   120 = muy lento (actual, da tiempo al servo a estabilizar)
#define MS_POR_PASO 120

// Pausa entre fases (recoger -> soltar) en ms.
// Cuanto más grande, más tiempo tiene la pinza para agarrar/soltar bien.
//   1000 = pausa corta (pinza apenas reacciona)
//   2000 = pinza estabiliza bien (actual, recomendado)
//   3000 = pausa "dramática"
#define PAUSA_AGARRE 2000

// Baudios del puerto serie (debe coincidir con Python: 9600)
#define BAUDIOS 9600

// ──────────────────────────────────────────────
// ESTADO GLOBAL
// ──────────────────────────────────────────────

Servo servoBase;
Servo servoBrazo1;
Servo servoBrazo2;
#ifdef USAR_PINZA
Servo servoPinza;
#endif

// Estado actual de los servos (se inicializa en setup() con los valores PARKED_*)
int anguloBase   = PARKED_BASE;
int anguloBrazo1 = PARKED_BRAZO1;
int anguloBrazo2 = PARKED_BRAZO2;

// Buffer de entrada
String buffer = "";

// ──────────────────────────────────────────────
// SETUP
// ──────────────────────────────────────────────

void setup() {
  Serial.begin(BAUDIOS);
  Serial.setTimeout(50);

  servoBase.attach(PIN_BASE);
  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);
#ifdef USAR_PINZA
  servoPinza.attach(PIN_PINZA);
  servoPinza.write(PARKED_PINZA);
#endif

  // Posición inicial = parked
  servoBase.write(anguloBase);
  servoBrazo1.write(anguloBrazo1);
  servoBrazo2.write(anguloBrazo2);

  buffer.reserve(64);
  delay(500);
  Serial.println("READY");
}

// ──────────────────────────────────────────────
// LOOP
// ──────────────────────────────────────────────

void loop() {
  while (Serial.available() > 0) {
    char c = (char) Serial.read();
    if (c == '\n') {
      procesarLinea(buffer);
      buffer = "";
    } else if (c != '\r') {
      buffer += c;
      if (buffer.length() > 80) {
        // Línea sospechosamente larga: descartar
        buffer = "";
        Serial.println("ERR linea muy larga");
      }
    }
  }
}

// ──────────────────────────────────────────────
// PARSEO Y EJECUCIÓN
// ──────────────────────────────────────────────

void procesarLinea(const String& linea) {
  String s = linea;
  s.trim();
  if (s.length() == 0) return;

  // Comando especial: HOME / PARK -> volver a posición parked
  if (s.equalsIgnoreCase("HOME") || s.equalsIgnoreCase("PARK")) {
    irAParked();
    Serial.println("OK");
    return;
  }

  // Comando especial: PING -> diagnóstico
  if (s.equalsIgnoreCase("PING")) {
    Serial.println("PONG");
    return;
  }

  // Formato esperado: "B,B1,B2|B,B1,B2"
  int sep = s.indexOf('|');
  if (sep < 0) {
    Serial.println("ERR falta separador |");
    return;
  }

  String parteA = s.substring(0, sep);
  String parteB = s.substring(sep + 1);

  int b1, br1_1, br2_1;
  int b2, br1_2, br2_2;
  if (!parsearTresAngulos(parteA, b1, br1_1, br2_1)) {
    Serial.println("ERR parseo origen");
    return;
  }
  if (!parsearTresAngulos(parteB, b2, br1_2, br2_2)) {
    Serial.println("ERR parseo destino");
    return;
  }

  if (!enRangoBase(b1) || !enRangoBrazo1(br1_1) || !enRangoBrazo2(br2_1) ||
      !enRangoBase(b2) || !enRangoBrazo1(br1_2) || !enRangoBrazo2(br2_2)) {
    Serial.println("ERR angulo fuera de rango");
    return;
  }

  // FASE 1 — ir a la posición de origen y "tomar" la pieza
  moverA(b1, br1_1, br2_1);
#ifdef USAR_PINZA
  servoPinza.write(PINZA_CERRADA);
#endif
  delay(PAUSA_AGARRE);

  // FASE 2 — ir a la posición de destino y "soltar"
  moverA(b2, br1_2, br2_2);
#ifdef USAR_PINZA
  servoPinza.write(PINZA_ABIERTA);
#endif
  delay(PAUSA_AGARRE);

  // FASE 3 — volver a posición parked (libera el tablero para que el humano juegue)
  irAParked();

  Serial.println("OK");
}

void irAParked() {
  moverA(PARKED_BASE, PARKED_BRAZO1, PARKED_BRAZO2);
#ifdef USAR_PINZA
  servoPinza.write(PARKED_PINZA);
#endif
  delay(200);
}

bool parsearTresAngulos(const String& s, int& a, int& b, int& c) {
  int p1 = s.indexOf(',');
  int p2 = s.indexOf(',', p1 + 1);
  if (p1 < 0 || p2 < 0) return false;
  a = (int) round(s.substring(0, p1).toFloat());
  b = (int) round(s.substring(p1 + 1, p2).toFloat());
  c = (int) round(s.substring(p2 + 1).toFloat());
  return true;
}

bool enRangoBase(int v)   { return v >= BASE_MIN   && v <= BASE_MAX;   }
bool enRangoBrazo1(int v) { return v >= BRAZO1_MIN && v <= BRAZO1_MAX; }
bool enRangoBrazo2(int v) { return v >= BRAZO2_MIN && v <= BRAZO2_MAX; }

// ──────────────────────────────────────────────
// MOVIMIENTO SUAVE (interpolación 1° a 1°)
// ──────────────────────────────────────────────

void moverA(int destBase, int destBrazo1, int destBrazo2) {
  int diffBase   = destBase   - anguloBase;
  int diffBrazo1 = destBrazo1 - anguloBrazo1;
  int diffBrazo2 = destBrazo2 - anguloBrazo2;

  int pasos = max(max(abs(diffBase), abs(diffBrazo1)), abs(diffBrazo2));
  if (pasos == 0) return;

  for (int i = 1; i <= pasos; i++) {
    int b   = anguloBase   + (long) diffBase   * i / pasos;
    int br1 = anguloBrazo1 + (long) diffBrazo1 * i / pasos;
    int br2 = anguloBrazo2 + (long) diffBrazo2 * i / pasos;
    servoBase.write(b);
    servoBrazo1.write(br1);
    servoBrazo2.write(br2);
    delay(MS_POR_PASO);
  }

  anguloBase   = destBase;
  anguloBrazo1 = destBrazo1;
  anguloBrazo2 = destBrazo2;
}
