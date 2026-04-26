// calibracion_servo.ino
// Estira los 3 servos del brazo a 170° y cierra la pinza, para poder
// medir L1 (hombro→codo), L2 (codo→pinza) y H (altura del hombro al tablero).
//
// Pines (mismos del sketch principal):
//   - Servo BASE              -> D3
//   - Servo BRAZO 1 (hombro)  -> D6   (el que sube y baja)
//   - Servo BRAZO 2 (muñeca)  -> D10
//   - Servo PINZA             -> D11  (0=abre, 60=cierra)
//
// Cómo medir cuando esté estirado:
//   1. Subí este sketch.
//   2. Esperá que el brazo termine de extenderse.
//   3. L1 = del eje del HOMBRO al eje del CODO/MUÑECA (cm).
//   4. L2 = del eje del CODO/MUÑECA a la PUNTA de la pinza CERRADA (cm).
//   5. H  = del eje del HOMBRO al PLANO del tablero (cm).
//
// IMPORTANTE: si oís un servo zumbar fuerte o se calienta, desconectá YA.
// Probablemente está stalleando contra un tope mecánico.

#include <Servo.h>

#define PIN_BASE    3
#define PIN_BRAZO1  6   // hombro (sube y baja)
#define PIN_BRAZO2  10  // muñeca
#define PIN_PINZA   11

// Posiciones para estirar el brazo
#define ANGULO_ESTIRADO   180   // los 3 servos del brazo
#define ANGULO_PINZA      60    // pinza cerrada (para medir L2 hasta la punta)

Servo servoBase;
Servo servoBrazo1;
Servo servoBrazo2;
Servo servoPinza;

void setup() {
  Serial.begin(9600);

  servoBase.attach(PIN_BASE);
  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);
  servoPinza.attach(PIN_PINZA);

  // Empezar centrados (90°) para tener un punto de partida conocido
  servoBase.write(90);
  servoBrazo1.write(90);
  servoBrazo2.write(90);
  servoPinza.write(0);
  delay(1500);

  Serial.println(F(""));
  Serial.println(F("=== CALIBRACION: ESTIRANDO BRAZO A 170 ==="));
  Serial.println(F("Movimiento suave de 90 -> 170..."));

  // Mover suavemente de 90 a 170 (1° por paso, 30 ms entre pasos)
  for (int a = 90; a <= ANGULO_ESTIRADO; a++) {
    servoBase.write(a);
    servoBrazo1.write(a);
    servoBrazo2.write(a);
    delay(30);
  }

  // Cerrar la pinza para medir L2 hasta la punta
  delay(500);
  servoPinza.write(ANGULO_PINZA);

  Serial.println(F("Listo. Brazo estirado a 170, pinza cerrada en 60."));
  Serial.println(F("Ahora medi L1, L2 y H con regla."));
}

void loop() {
  // Mantener servos fijos en la posición estirada
  servoBase.write(ANGULO_ESTIRADO);
  servoBrazo1.write(ANGULO_ESTIRADO);
  servoBrazo2.write(ANGULO_ESTIRADO);
  servoPinza.write(ANGULO_PINZA);
  delay(500);
}
