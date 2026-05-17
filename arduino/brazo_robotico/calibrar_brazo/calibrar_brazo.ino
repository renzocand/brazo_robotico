// calibrar_brazo.ino — CALIBRAR LOS DOS SERVOS DEL BRAZO JUNTOS
//
// BRAZO1 (D6, hombro) y BRAZO2 (D10, muneca) se mueven en SINCRONIA.
// Asi el movimiento es coherente — el brazo no termina en una pose rara
// como cuando se mueve solo uno.
//
// La BASE (D3) y la PINZA (D11) quedan APAGADAS (sin pulso PWM, no zumban).
//
// Flujo:
//   1. Lleva brazo1+brazo2 a 90 (centro). Pausa para escuchar.
//   2. SUBE de a 1 grado lentamente (90 -> 175). Manda algo cuando zumbe.
//   3. Vuelve a 90.
//   4. BAJA de a 1 grado lentamente (90 -> 5). Manda algo cuando zumbe.
//   5. Vuelve a 90.
//   6. Imprime resumen con el rango seguro.
//
// Si NO zumba en una direccion, llega al cap y queda marcado con *.
//
// Como pararlo de emergencia:
//   - Manda cualquier letra + Enter por Serial Monitor.
//   - O apreta RESET en el Arduino.
//   - O desconecta el USB.

#include <Servo.h>

#define PIN_BRAZO1      6     // hombro
#define PIN_BRAZO2      10    // muneca

#define MS_POR_PASO     200   // lento para que se oiga bien si zumba
#define ANGULO_CENTRO   90
#define ANGULO_CAP_MAX  175   // no nos arriesgamos al 180 (tope mecanico)
#define ANGULO_CAP_MIN  5     // ni al 0
#define MARGEN_SEG      5     // grados que se le quitan/suman al limite raw

Servo servoBrazo1;
Servo servoBrazo2;

int anguloMin = ANGULO_CAP_MIN;
int anguloMax = ANGULO_CAP_MAX;
bool zumboSubiendo = false;
bool zumboBajando  = false;

void setup() {
  Serial.begin(9600);
  delay(800);

  Serial.println();
  Serial.println(F("======================================================"));
  Serial.println(F("  CALIBRACION BRAZO COMPLETO (BRAZO1 D6 + BRAZO2 D10)"));
  Serial.println(F("======================================================"));
  Serial.println(F("Los DOS servos se mueven en sincronia."));
  Serial.println(F("BASE y PINZA estan APAGADAS (no zumban)."));
  Serial.println(F("Cuando oigas ZUMBAR, manda cualquier letra + Enter."));
  Serial.println();
  delay(2500);

  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);
  moverAmbos(ANGULO_CENTRO);
  delay(1500);

  // ── Fase 1: SUBIR desde centro ──
  Serial.println(F(">>> Fase 1: SUBIENDO desde 90."));
  Serial.println(F("    Manda algo cuando zumbe."));
  vaciarSerial();
  int aFinal = ANGULO_CAP_MAX;
  for (int a = ANGULO_CENTRO + 1; a <= ANGULO_CAP_MAX; a++) {
    moverAmbos(a);
    Serial.print(F("    angulo = "));
    Serial.println(a);
    if (Serial.available() > 0) {
      vaciarSerial();
      anguloMax = a;
      zumboSubiendo = true;
      aFinal = a;
      Serial.print(F("    [REGISTRADO MAX = "));
      Serial.print(a);
      Serial.println(F("]"));
      break;
    }
    delay(MS_POR_PASO);
  }
  if (!zumboSubiendo) {
    Serial.print(F("    [NO ZUMBO. Llego al cap "));
    Serial.print(ANGULO_CAP_MAX);
    Serial.println(F("]"));
  }

  // Volver al centro
  Serial.println(F("    Volviendo al centro..."));
  for (int a = aFinal; a >= ANGULO_CENTRO; a--) {
    moverAmbos(a);
    delay(MS_POR_PASO / 2);
  }
  delay(1500);

  // ── Fase 2: BAJAR desde centro ──
  Serial.println();
  Serial.println(F(">>> Fase 2: BAJANDO desde 90."));
  Serial.println(F("    Manda algo cuando zumbe."));
  vaciarSerial();
  aFinal = ANGULO_CAP_MIN;
  for (int a = ANGULO_CENTRO - 1; a >= ANGULO_CAP_MIN; a--) {
    moverAmbos(a);
    Serial.print(F("    angulo = "));
    Serial.println(a);
    if (Serial.available() > 0) {
      vaciarSerial();
      anguloMin = a;
      zumboBajando = true;
      aFinal = a;
      Serial.print(F("    [REGISTRADO MIN = "));
      Serial.print(a);
      Serial.println(F("]"));
      break;
    }
    delay(MS_POR_PASO);
  }
  if (!zumboBajando) {
    Serial.print(F("    [NO ZUMBO. Llego al cap "));
    Serial.print(ANGULO_CAP_MIN);
    Serial.println(F("]"));
  }

  // Volver al centro y apagar
  Serial.println(F("    Volviendo al centro..."));
  for (int a = aFinal; a <= ANGULO_CENTRO; a++) {
    moverAmbos(a);
    delay(MS_POR_PASO / 2);
  }
  delay(1500);
  servoBrazo1.detach();
  servoBrazo2.detach();

  imprimirResumen();
}

void loop() {
  delay(1000);
}

void moverAmbos(int angulo) {
  servoBrazo1.write(angulo);
  servoBrazo2.write(angulo);
}

void vaciarSerial() {
  while (Serial.available() > 0) Serial.read();
}

void imprimirResumen() {
  int min_seg = zumboBajando  ? anguloMin + MARGEN_SEG : anguloMin;
  int max_seg = zumboSubiendo ? anguloMax - MARGEN_SEG : anguloMax;

  Serial.println();
  Serial.println();
  Serial.println(F("====================================================="));
  Serial.println(F("    RESUMEN: BRAZO COMPLETO (BRAZO1 + BRAZO2)"));
  Serial.println(F("====================================================="));
  Serial.print(F("  MIN raw: "));
  Serial.print(anguloMin);
  Serial.println(zumboBajando ? F("") : F("*"));
  Serial.print(F("  MAX raw: "));
  Serial.print(anguloMax);
  Serial.println(zumboSubiendo ? F("") : F("*"));
  Serial.println();
  Serial.print(F("  RANGO SEGURO (con margen "));
  Serial.print(MARGEN_SEG);
  Serial.print(F("): "));
  Serial.print(min_seg);
  Serial.print(F(" a "));
  Serial.println(max_seg);
  Serial.println();
  Serial.println(F("(*) No zumbo en esa direccion: limite = cap del barrido."));
  Serial.println();
  Serial.println(F("Como ambos servos se movieron juntos, el rango aplica a"));
  Serial.println(F("AMBOS. Copia los valores a:"));
  Serial.println(F("  config.py:"));
  Serial.println(F("    SERVO_BRAZO1_MIN / SERVO_BRAZO1_MAX"));
  Serial.println(F("    SERVO_BRAZO2_MIN / SERVO_BRAZO2_MAX"));
  Serial.println(F("  brazo_robotico.ino:"));
  Serial.println(F("    BRAZO1_MIN / BRAZO1_MAX"));
  Serial.println(F("    BRAZO2_MIN / BRAZO2_MAX"));
  Serial.println();
  Serial.println(F("=== FIN ==="));
}
