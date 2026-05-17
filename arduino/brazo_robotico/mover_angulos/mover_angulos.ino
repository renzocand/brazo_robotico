/*
  mover_angulos.ino

  Mueve el brazo COMPLETO (BASE, BRAZO1, BRAZO2) desde ángulos de
  inicio hasta ángulos objetivo lentamente, mantiene la posición unos
  segundos y vuelve a la posición "base" (parked).

  Seguridad (comentario):
    RESUMEN: BRAZO COMPLETO (BRAZO1 + BRAZO2)
    MIN raw: 83
    MAX raw: 167

    RANGO SEGURO (con margen 5): 88 a 160

  Edita las variables `START_*` y `TARGET_*` más abajo para indicar
  los ángulos de inicio y destino. Respeta los rangos seguros.

  Uso:
    - Abrí en el IDE de Arduino y subí el sketch.
    - Abrí el Monitor Serial a 9600 para ver mensajes.
    - Enviá cualquier caracter por Serial para detener la ejecución.

*/

#include <Servo.h>

#define PIN_BASE   3
#define PIN_BRAZO1 6
#define PIN_BRAZO2 10
#define PIN_PINZA   11

// --- Ajusta aquí los ángulos de inicio y objetivo ---
// Valores de inicio (posición desde la que arrancan)
const int START_BASE   = 120;
const int START_BRAZO1 = 90;
const int START_BRAZO2 = 90;
const int START_PINZA  = 60; // pinza cerrad

// Valores objetivo (a donde quieres que vaya el brazo)
const int TARGET_BASE   = 120; // 90 era b2
const int TARGET_BRAZO1 = 40;
const int TARGET_BRAZO2 = 130;
// ----------------------------------------------------

// Ángulos de pinza
const int PINZA_ABIERTA = 0;
const int PINZA_CERRADA = 60;

// Tiempo que mantiene la posición objetivo (ms)
const unsigned long HOLD_MS = 3000; // 3 segundos

// Velocidad: ms entre cada paso de 1° (mayor = más lento)
const unsigned int MS_POR_PASO = 100; // movimiento lento

// Posición al final del ciclo: regresa a la posición inicial
const int RETURN_BASE   = START_BASE;
const int RETURN_BRAZO1 = START_BRAZO1;
const int RETURN_BRAZO2 = START_BRAZO2;

Servo servoBase;
Servo servoBrazo1;
Servo servoBrazo2;
Servo servoPinza;

// Estado actual (se actualiza conforme se escriben ángulos)
int angBase;
int angBrazo1;
int angBrazo2;

bool detenido = false;

void setup() {
  Serial.begin(9600);
  delay(200);

  servoBase.attach(PIN_BASE);
  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);
  servoPinza.attach(PIN_PINZA);

  Serial.println();
  Serial.println(F("mover_angulos: iniciando"));
  Serial.println(F("Enviar cualquier caracter por Serial para detener."));
  Serial.println();

  // Inicializar en START_*
  angBase   = clampAngle(START_BASE);
  angBrazo1 = clampAngle(START_BRAZO1);
  angBrazo2 = clampAngle(START_BRAZO2);

  servoBase.write(angBase);
  servoBrazo1.write(angBrazo1);
  servoBrazo2.write(angBrazo2);
  servoPinza.write(START_PINZA);
  delay(800);

  // Abrir la pinza antes del movimiento
  Serial.println(F("Abriendo la pinza antes de mover..."));
  servoPinza.write(PINZA_ABIERTA);
  delay(700);

  // Mover los tres servos simultáneamente hacia TARGET_*
  moverTodosASuave(TARGET_BASE, TARGET_BRAZO1, TARGET_BRAZO2, MS_POR_PASO);
  if (detenido) return;

  // Cerrar la pinza en el destino
  Serial.println(F("En destino. Cerrando pinza..."));
  servoPinza.write(PINZA_CERRADA);
  delay(700);

  // Mantener la posicion objetivo con pinza cerrada
  Serial.println(F("En objetivo con pinza cerrada. Manteniendo..."));
  unsigned long inicio = millis();
  while (millis() - inicio < HOLD_MS) {
    if (Serial.available() > 0) { detenerPorSerial(); return; }
    delay(50);
  }

  // Asegurar que la pinza está cerrada antes de regresar
  Serial.println(F("Asegurando la pinza cerrada antes de regresar..."));
  servoPinza.write(PINZA_CERRADA);
  delay(700);

  // Volver a la posición inicial lentamente, con la pinza cerrada
  Serial.println(F("Regresando a la posicion inicial con pinza cerrada..."));
  moverTodosASuave(RETURN_BASE, RETURN_BRAZO1, RETURN_BRAZO2, MS_POR_PASO);
  if (detenido) return;

  // Mantener la pinza cerrada al final
  servoPinza.write(PINZA_CERRADA);
  delay(200);

  Serial.println(F("Listo. Mantengo la posicion inicial con pinza cerrada."));
}

void loop() {
  if (Serial.available() > 0) {
    detenerPorSerial();
  }
  delay(100);
}

// Mueve los tres servos simultáneamente grado a grado hasta los objetivos.
void moverTodosASuave(int targetBase, int targetB1, int targetB2, unsigned int msPaso) {
  targetBase = clampAngle(targetBase);
  targetB1   = clampAngle(targetB1);
  targetB2   = clampAngle(targetB2);

  Serial.print(F("Moviendo a: BASE=")); Serial.print(targetBase);
  Serial.print(F("  B1=")); Serial.print(targetB1);
  Serial.print(F("  B2=")); Serial.println(targetB2);

  while ((angBase != targetBase) || (angBrazo1 != targetB1) || (angBrazo2 != targetB2)) {
    if (Serial.available() > 0) { detenerPorSerial(); return; }

    if (angBase < targetBase) angBase++; else if (angBase > targetBase) angBase--;
    if (angBrazo1 < targetB1) angBrazo1++; else if (angBrazo1 > targetB1) angBrazo1--;
    if (angBrazo2 < targetB2) angBrazo2++; else if (angBrazo2 > targetB2) angBrazo2--;

    servoBase.write(angBase);
    servoBrazo1.write(angBrazo1);
    servoBrazo2.write(angBrazo2);

    delay(msPaso);
  }
}

// Ajuste simple: asegura ángulos entre 0 y 180
int clampAngle(int a) {
  if (a < 0) return 0;
  if (a > 180) return 180;
  return a;
}

void detenerPorSerial() {
  while (Serial.available() > 0) Serial.read();
  detenido = true;
  Serial.println(F("DETENIDO por entrada serial."));
}
