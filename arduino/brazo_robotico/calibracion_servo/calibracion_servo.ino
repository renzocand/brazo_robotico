// calibracion_servo.ino — MODO IDENTIFICAR QUE SERVO ZUMBA
//
// Activa UN servo a la vez (los otros desconectados, sin recibir señal),
// lo deja en su ángulo de test unos segundos, y avisa por Serial cuál está
// activo. Si oís zumbido, mirá la consola: ese es el servo problemático.
//
// Pines (mismos del sketch principal):
//   - Servo BASE              -> D3
//   - Servo BRAZO 1 (hombro)  -> D6   (el que sube y baja)
//   - Servo BRAZO 2 (muñeca)  -> D10
//   - Servo PINZA             -> D11
//
// Ángulos de test:
//   BASE, BRAZO1, BRAZO2 → 90°
//   PINZA → alterna entre ABIERTA (0°) y CERRADA (60°) para verificar las dos
//           posiciones reales del gripper.
//
// Cómo usarlo:
//   1. Subí el sketch.
//   2. Abrí el Serial Monitor a 9600 baudios.
//   3. Vas a leer:  ">>> AHORA SOLO ACTIVO: BASE (D3) — escucha 6 seg"
//      y solo el servo BASE recibe pulso PWM. Los otros 3 quedan inertes.
//   4. Si NO zumba ningún servo durante esos 6 seg → BASE está bien.
//      Si zumba algo → el problema es BASE.
//   5. Pasa al siguiente y repite.
//
// Cómo PARARLO:
//   - Mandá cualquier letra + Enter por Serial Monitor → freeza todo.
//   - O apretá RESET en el Arduino.
//   - O desconectá el USB.

#include <Servo.h>

#define PIN_BASE    3
#define PIN_BRAZO1  6
#define PIN_BRAZO2  10
#define PIN_PINZA   11

#define ANGULO_BRAZO_TEST   90    // base, brazo1, brazo2 en su test
#define PINZA_ABIERTA       0
#define PINZA_CERRADA       60
#define SEG_POR_SERVO       6     // segundos que cada servo queda activo y solo

Servo servoBase;
Servo servoBrazo1;
Servo servoBrazo2;
Servo servoPinza;

bool detenido = false;

void setup() {
  Serial.begin(9600);
  delay(800);

  Serial.println();
  Serial.println(F("=== DIAGNOSTICO: QUE SERVO ZUMBA ==="));
  Serial.println(F("Voy a activar UN servo a la vez. Si zumba algo,"));
  Serial.println(F("el culpable es el que aparezca como ACTIVO en pantalla."));
  Serial.println(F("Para parar: manda cualquier letra y Enter."));
  Serial.println();
  delay(2000);
}

void loop() {
  if (detenido) { delay(500); return; }

  probarBrazo("BASE   (rotacion, D3)", servoBase,   PIN_BASE);
  if (detenido) return;

  probarBrazo("BRAZO1 (hombro, D6)",   servoBrazo1, PIN_BRAZO1);
  if (detenido) return;

  probarBrazo("BRAZO2 (muneca, D10)",  servoBrazo2, PIN_BRAZO2);
  if (detenido) return;

  probarPinza();
  if (detenido) return;

  Serial.println();
  Serial.println(F("=== CICLO COMPLETO. Apreta RESET para repetir. ==="));
  detenido = true;
}

// Apaga todos los servos, activa solo el indicado en ANGULO_BRAZO_TEST,
// y lo deja sonando (o en silencio) durante SEG_POR_SERVO segundos.
void probarBrazo(const char* nombre, Servo& servo, int pin) {
  apagarTodos();

  Serial.println();
  Serial.print(F(">>> AHORA SOLO ACTIVO: "));
  Serial.println(nombre);
  Serial.print(F("    Angulo fijo: "));
  Serial.print(ANGULO_BRAZO_TEST);
  Serial.print(F(", durante "));
  Serial.print(SEG_POR_SERVO);
  Serial.println(F(" segundos."));

  servo.attach(pin);
  servo.write(ANGULO_BRAZO_TEST);

  esperar(SEG_POR_SERVO * 1000UL, nombre);
}

// Apaga todos, activa solo la pinza, y la abre/cierra alternando.
void probarPinza() {
  apagarTodos();

  Serial.println();
  Serial.println(F(">>> AHORA SOLO ACTIVO: PINZA  (gripper, D11)"));
  Serial.print(F("    Alternando ABIERTA ("));
  Serial.print(PINZA_ABIERTA);
  Serial.print(F(") y CERRADA ("));
  Serial.print(PINZA_CERRADA);
  Serial.println(F(") cada 1.5 seg."));

  servoPinza.attach(PIN_PINZA);

  // Alterna abrir/cerrar durante SEG_POR_SERVO segundos
  unsigned long inicio = millis();
  bool cerrada = false;
  while (millis() - inicio < (unsigned long)SEG_POR_SERVO * 1000UL) {
    cerrada = !cerrada;
    int angulo = cerrada ? PINZA_CERRADA : PINZA_ABIERTA;
    servoPinza.write(angulo);
    Serial.print(F("    PINZA -> "));
    Serial.println(cerrada ? F("CERRADA") : F("ABIERTA"));
    if (esperar(1500, "PINZA  (gripper, D11)")) return;
  }
}

void apagarTodos() {
  servoBase.detach();
  servoBrazo1.detach();
  servoBrazo2.detach();
  servoPinza.detach();
  delay(300);
}

// Espera N ms chequeando STOP cada 100ms. Devuelve true si se detuvo.
bool esperar(unsigned long ms, const char* nombreActivo) {
  unsigned long inicio = millis();
  while (millis() - inicio < ms) {
    if (Serial.available() > 0) {
      while (Serial.available() > 0) Serial.read();
      detenido = true;
      Serial.println();
      Serial.print(F("!!! DETENIDO. Servo activo cuando se detuvo: "));
      Serial.println(nombreActivo);
      Serial.println(F("Si estabas oyendo zumbido, este es el problematico."));
      return true;
    }
    delay(100);
  }
  return false;
}
