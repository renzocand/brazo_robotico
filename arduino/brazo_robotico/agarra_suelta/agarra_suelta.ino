// test_servos.ino — TEST RAPIDO: ¿FUNCIONAN / ESTAN CONECTADOS LOS SERVOS?
//
// Mueve UN servo a la vez con un barrido suave y visible, mientras los
// otros 3 se quedan QUIETOS sosteniendo la pose (el brazo no se desarma).
//
// Para cada servo:
//   1. Avisa por Serial cuál va a probar.
//   2. Lo lleva centro -> minimo -> maximo -> centro, lento, 1° a la vez.
//   3. Vos MIRAS ese servo:
//        - Se mueve  -> esta conectado y funciona.
//        - NO se mueve / vibra raro -> cable de senal suelto, sin
//          alimentacion, o servo quemado.
//
// Pines y rangos: los MISMOS del sketch principal (brazo_robotico.ino).
//   BASE   D3   rango seguro 10-170
//   BRAZO1 D6   rango seguro 73-150  (hombro, sube y baja)
//   BRAZO2 D10  rango seguro 73-150  (muneca)
//   PINZA  D11  0 abierta / 60 cerrada
//
// El barrido se mantiene BIEN ADENTRO de los rangos seguros para no
// forzar ningun servo contra un tope.
//
// Como usarlo:
//   1. Subi este sketch al Arduino.
//   2. Abri el Serial Monitor a 9600 baudios.
//   3. Segui en pantalla que servo se esta probando y miralo.
//
// Como pararlo:
//   - Manda cualquier letra + Enter por el Serial Monitor -> freeza todo.
//   - O apreta RESET en el Arduino.
//
// Cuando termines, volve a subir brazo_robotico.ino para jugar.

#include <Servo.h>

#define PIN_BASE    3
#define PIN_BRAZO1  6
#define PIN_BRAZO2  10
#define PIN_PINZA   11

// Pose de reposo: donde se quedan los servos que NO se estan probando.
#define REPOSO_BASE     90
#define REPOSO_BRAZO1   90
#define REPOSO_BRAZO2   90

// Pinza
#define PINZA_ABIERTA   0
#define PINZA_CERRADA   60

// Barrido de cada servo: centro -> MIN -> MAX -> centro.
// Todos los valores estan dentro del rango seguro de cada servo.
#define BASE_CENTRO     90
#define BASE_MIN_TEST   50
#define BASE_MAX_TEST   130

#define BRAZO1_CENTRO   90
#define BRAZO1_MIN_TEST 80
#define BRAZO1_MAX_TEST 130

#define BRAZO2_CENTRO   90
#define BRAZO2_MIN_TEST 80
#define BRAZO2_MAX_TEST 130

#define MS_POR_PASO     15      // ms entre cada grado del barrido (suave)
#define PAUSA_MS        1200    // pausa en cada extremo

Servo servoBase;
Servo servoBrazo1;
Servo servoBrazo2;
Servo servoPinza;

bool detenido = false;

void setup() {
  Serial.begin(9600);
  delay(800);

  // Todos los servos quedan ATTACHED y sosteniendo su pose, asi el brazo
  // no se afloja mientras probamos uno por uno.
  servoBase.attach(PIN_BASE);
  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);
  servoPinza.attach(PIN_PINZA);

  servoBase.write(REPOSO_BASE);
  servoBrazo1.write(REPOSO_BRAZO1);
  servoBrazo2.write(REPOSO_BRAZO2);
  servoPinza.write(PINZA_CERRADA);
  delay(1000);

  Serial.println();
  Serial.println(F("==================================================="));
  Serial.println(F("   TEST DE SERVOS — ?se mueven? ?estan conectados?"));
  Serial.println(F("==================================================="));
  Serial.println(F("Voy a mover UN servo a la vez. Mira ese servo:"));
  Serial.println(F("  - Se mueve         -> OK, conectado."));
  Serial.println(F("  - NO se mueve      -> cable suelto / sin corriente."));
  Serial.println(F("Para parar: manda cualquier letra + Enter."));
  Serial.println();
  delay(2500);
}

void loop() {
  if (detenido) { delay(500); return; }

  probarServo(F("BASE   (rotacion, D3)"),  servoBase,
              BASE_CENTRO,   BASE_MIN_TEST,   BASE_MAX_TEST);
  if (detenido) return;

  probarServo(F("BRAZO1 (hombro,   D6)"),  servoBrazo1,
              BRAZO1_CENTRO, BRAZO1_MIN_TEST, BRAZO1_MAX_TEST);
  if (detenido) return;

  probarServo(F("BRAZO2 (muneca,  D10)"),  servoBrazo2,
              BRAZO2_CENTRO, BRAZO2_MIN_TEST, BRAZO2_MAX_TEST);
  if (detenido) return;

  probarPinza();
  if (detenido) return;

  Serial.println();
  Serial.println(F("=== CICLO COMPLETO. Apreta RESET para repetir el test. ==="));
  detenido = true;
}

// Barre un servo centro -> min -> max -> centro, lento y visible.
void probarServo(const __FlashStringHelper* nombre, Servo& servo,
                 int centro, int minTest, int maxTest) {
  Serial.println();
  Serial.print(F(">>> PROBANDO: "));
  Serial.println(nombre);
  Serial.print(F("    Barrido: "));
  Serial.print(centro); Serial.print(F(" -> "));
  Serial.print(minTest); Serial.print(F(" -> "));
  Serial.print(maxTest); Serial.print(F(" -> "));
  Serial.println(centro);
  Serial.println(F("    MIRA este servo ahora."));

  if (barrer(servo, centro,  minTest)) return;
  pausa();
  if (barrer(servo, minTest, maxTest)) return;
  pausa();
  if (barrer(servo, maxTest, centro))  return;
  pausa();

  Serial.print(F("    [Listo. ?Se movio "));
  Serial.print(nombre);
  Serial.println(F("? Si NO -> revisa ese servo.]"));
}

// Abre y cierra la pinza un par de veces.
void probarPinza() {
  Serial.println();
  Serial.println(F(">>> PROBANDO: PINZA  (gripper, D11)"));
  Serial.println(F("    Abriendo y cerrando. MIRA la pinza ahora."));

  for (int i = 0; i < 3; i++) {
    Serial.println(F("    PINZA -> ABIERTA"));
    servoPinza.write(PINZA_ABIERTA);
    if (esperar(900)) return;
    Serial.println(F("    PINZA -> CERRADA"));
    servoPinza.write(PINZA_CERRADA);
    if (esperar(900)) return;
  }
  Serial.println(F("    [Listo. ?Abrio y cerro la pinza? Si NO -> revisala.]"));
}

// Mueve `servo` de `desde` a `hasta` de a 1 grado. Devuelve true si se detuvo.
bool barrer(Servo& servo, int desde, int hasta) {
  int paso = (hasta >= desde) ? 1 : -1;
  for (int a = desde; a != hasta; a += paso) {
    servo.write(a);
    if (chequearStop()) return true;
    delay(MS_POR_PASO);
  }
  servo.write(hasta);
  return false;
}

void pausa() {
  esperar(PAUSA_MS);
}

// Espera N ms revisando STOP. Devuelve true si se pidio parar.
bool esperar(unsigned long ms) {
  unsigned long inicio = millis();
  while (millis() - inicio < ms) {
    if (chequearStop()) return true;
    delay(20);
  }
  return false;
}

// Devuelve true (y marca detenido) si llego algo por Serial.
bool chequearStop() {
  if (Serial.available() > 0) {
    while (Serial.available() > 0) Serial.read();
    detenido = true;
    Serial.println();
    Serial.println(F("!!! DETENIDO por el usuario."));
    return true;
  }
  return false;
}
