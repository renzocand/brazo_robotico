/*
  sequence_b2_f6.ino

  Secuencia preconfigurada: coger pieza en B2, mover a F6, soltar, volver a base.

  ATENCIÓN: Algunos ángulos pueden estar fuera del rango seguro de tus
  servos. Ejecuta bajo tu responsabilidad y detén con cualquier caracter
  por Serial si algo zumba o choca.

*/

#include <Servo.h>

#define PIN_BASE   3
#define PIN_BRAZO1 6
#define PIN_BRAZO2 10
#define PIN_PINZA  11

// --- Posiciones de inicio (BASE) ---
const int START_BASE   = 90;
const int START_BRAZO1 = 90;
const int START_BRAZO2 = 90;
const int START_PINZA  = 60; // pinza cerrada

// --- Posición B2 (recoger) ---
const int B2_BASE   = 88; // proporcionado
const int B2_BRAZO1 = 140;
const int B2_BRAZO2 = 172;

// --- Posición F6 (depositar) ---
const int F6_BASE   = 130;
const int F6_BRAZO1 = 30;
const int F6_BRAZO2 = 140;

// Pinza
const int PINZA_ABIERTA = 0;
const int PINZA_CERRADA = 60;

// Velocidad y pausas
const unsigned int MS_POR_PASO = 25; // ms por grado (suave y responsivo)
const unsigned long PAUSA_ENTREPASOS = 600; // ms
const unsigned long PAUSA_ESTABILIZAR = 250; // ms para asentar posición

Servo servoBase;
Servo servoBrazo1;
Servo servoBrazo2;
Servo servoPinza;

int angBase, angBrazo1, angBrazo2;
bool detenido = false;

void moveServoTo(Servo &s, int &currentAngle, int target, unsigned int msPaso);
void moverBase(int targetBase);
void moverBrazos(int targetB1, int targetB2, bool brazo2Primero = false);
void abrirPinza();
void cerrarPinza();
int clampAngle(int a);

void setup() {
  Serial.begin(9600);
  delay(200);

  servoBase.attach(PIN_BASE);
  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);
  servoPinza.attach(PIN_PINZA);

  Serial.println();
  Serial.println(F("sequence_b2_f6: iniciando secuencia"));
  Serial.println(F("Enviar cualquier caracter por Serial para detener."));

  angBase = clampAngle(START_BASE);
  angBrazo1 = clampAngle(START_BRAZO1);
  angBrazo2 = clampAngle(START_BRAZO2);

  servoBase.write(angBase);
  servoBrazo1.write(angBrazo1);
  servoBrazo2.write(angBrazo2);
  servoPinza.write(START_PINZA);
  delay(800);

  Serial.print(F("Angulos iniciales: base=")); Serial.print(angBase);
  Serial.print(F(" brazo1=")); Serial.print(angBrazo1);
  Serial.print(F(" brazo2=")); Serial.println(angBrazo2);

  // 1) Abrir pinza antes de bajar a B2
  abrirPinza();

  // 2) Ir a B2: primero base, luego brazos juntos
  moverBase(B2_BASE);
  if (detenido) return;
  moverBrazos(B2_BRAZO1, B2_BRAZO2);
  if (detenido) return;

  // 3) Cerrar pinza para agarrar
  cerrarPinza();

  // 4) Volver a la posición inicial con la pieza en la pinza
  Serial.println(F("Regresando a la posicion inicial con la pieza..."));
  moverBase(START_BASE);
  if (detenido) return;
  moverBrazos(START_BRAZO1, START_BRAZO2);
  if (detenido) return;

  Serial.println(F("Posicion inicial alcanzada. Esperando antes de ir a F6..."));
  delay(2000);

  // 5) Ir a F6 cargando la pieza
  Serial.println(F("Moviendo a F6 con pieza..."));
  moverBase(F6_BASE);
  if (detenido) return;
  moverBrazos(F6_BRAZO1, F6_BRAZO2);
  if (detenido) return;

  // 6) Soltar en F6
  abrirPinza();

  // 7) Volver a base con la pinza abierta (pieza dejada en F6)
  Serial.println(F("Volviendo a base con la pinza abierta..."));
  // Primero retraer el brazo que eleva, luego el otro brazo y finalmente la base.
  delay(300); // pequeña pausa para asegurarnos que la pieza cae
  moverBrazos(START_BRAZO1, START_BRAZO2, true);
  if (detenido) return;
  moverBase(START_BASE);
  if (detenido) return;

  Serial.println(F("Secuencia completada."));
}

void loop() {
  if (Serial.available() > 0) {
    while (Serial.available() > 0) Serial.read();
    detenido = true;
    Serial.println(F("DETENIDO por entrada serial."));
  }
  delay(100);
}

// Mueve un servo desde su ángulo actual hasta 'target' en pasos de 1 grado.
// Actualiza la variable de estado pasada por referencia (currentAngle).
void moveServoTo(Servo &s, int &currentAngle, int target, unsigned int msPaso) {
  target = clampAngle(target);
  if (currentAngle == target) {
    Serial.print(F("Servo ya en objetivo: "));
    Serial.println(target);
    return;
  }
  Serial.print(F("Moviendo servo a: "));
  Serial.println(target);
  while (currentAngle != target) {
    if (Serial.available() > 0) { while (Serial.available() > 0) Serial.read(); detenido = true; Serial.println(F("DETENIDO durante movimiento")); return; }
    if (currentAngle < target) currentAngle++; else currentAngle--;
    s.write(currentAngle);
    Serial.print(F("  ang=")); Serial.println(currentAngle);
    delay(msPaso);
  }
}

// Girar base (usa moveServoTo para consistencia)
void moverBase(int targetBase) {
  Serial.print(F("Girando base a: "));
  Serial.println(targetBase);
  moveServoTo(servoBase, angBase, targetBase, MS_POR_PASO);
  delay(PAUSA_ESTABILIZAR);
}

// Mover brazos secuencialmente con opción de invertir el orden
void moverBrazos(int targetB1, int targetB2, bool brazo2Primero = false) {
  if (!brazo2Primero) {
    Serial.print(F("Moviendo brazo1 a: "));
    Serial.println(targetB1);
    moveServoTo(servoBrazo1, angBrazo1, targetB1, MS_POR_PASO);
    if (detenido) return;
    delay(PAUSA_ESTABILIZAR);

    Serial.print(F("Moviendo brazo2 a: "));
    Serial.println(targetB2);
    moveServoTo(servoBrazo2, angBrazo2, targetB2, MS_POR_PASO);
    if (detenido) return;
    delay(PAUSA_ESTABILIZAR);
  } else {
    Serial.print(F("Moviendo brazo2 a: "));
    Serial.println(targetB2);
    moveServoTo(servoBrazo2, angBrazo2, targetB2, MS_POR_PASO);
    if (detenido) return;
    delay(PAUSA_ESTABILIZAR);

    Serial.print(F("Moviendo brazo1 a: "));
    Serial.println(targetB1);
    moveServoTo(servoBrazo1, angBrazo1, targetB1, MS_POR_PASO);
    if (detenido) return;
    delay(PAUSA_ESTABILIZAR);
  }
}

void abrirPinza() {
  Serial.println(F("Abrir pinza..."));
  servoPinza.write(PINZA_ABIERTA);
  delay(1000);
}

void cerrarPinza() {
  Serial.println(F("Cerrar pinza..."));
  servoPinza.write(PINZA_CERRADA);
  delay(1000);
}

int clampAngle(int a) {
  if (a < 0) return 0;
  if (a > 180) return 180;
  return a;
}
