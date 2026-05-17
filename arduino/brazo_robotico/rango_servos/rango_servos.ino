// rango_servos.ino — ENCONTRAR RANGOS SEGUROS POR SERVO (UNO A LA VEZ)
//
// Por cada servo (BASE, BRAZO1, BRAZO2):
//   1. Lo activa SOLO a él (los demás detacheados, sin pulso).
//   2. Lo lleva a 90° y empieza a SUBIR de a 1° lentamente.
//   3. Cuando oigas zumbar → mandá cualquier letra + Enter.
//      Se anota ese ángulo como MAX y se vuelve a 90.
//   4. Después empieza a BAJAR desde 90 lentamente.
//   5. Cuando oigas zumbar → mandá cualquier letra + Enter.
//      Se anota ese ángulo como MIN y se vuelve a 90.
//   6. Pasa al próximo servo.
//
// Si un servo NO zumba en todo el barrido, llega al cap (5° abajo, 175° arriba)
// y eso queda registrado como límite (marcado con * en la tabla).
//
// Al final imprime un RESUMEN con los rangos de cada servo + margen seguro.
//
// La PINZA se omite a propósito — sus ángulos ya están definidos
// (PINZA_ABIERTA / PINZA_CERRADA) y el barrido la hace zumbar al pedo.
//
// Pines (mismos del sketch principal):
//   - BASE   D3 | BRAZO1 D6 | BRAZO2 D10

#include <Servo.h>

#define PIN_BASE    3
#define PIN_BRAZO1  6
#define PIN_BRAZO2  10
#define PIN_PINZA   11    // solo para detacharla al inicio, no se calibra

#define MS_POR_PASO     200   // lento para que se oiga bien si zumba
#define ANGULO_CENTRO   90
#define ANGULO_CAP_MAX  175   // no nos arriesgamos al 180 (tope mecánico)
#define ANGULO_CAP_MIN  5     // ni al 0
#define MARGEN_SEG      5     // grados que se le quitan al límite raw

#define N_SERVOS 3

struct Resultado {
  const char* nombre;
  int pin;
  int anguloMin;       // donde zumbó al bajar (o ANGULO_CAP_MIN si nunca)
  int anguloMax;       // donde zumbó al subir (o ANGULO_CAP_MAX si nunca)
  bool zumboSubiendo;
  bool zumboBajando;
};

Resultado resultados[N_SERVOS];

Servo servoBase, servoBrazo1, servoBrazo2, servoPinza;  // pinza solo para detacharla
Servo* servos[N_SERVOS];

void setup() {
  Serial.begin(9600);
  delay(800);

  resultados[0] = {"BASE   (rotacion, D3)", PIN_BASE,   ANGULO_CAP_MIN, ANGULO_CAP_MAX, false, false};
  resultados[1] = {"BRAZO1 (hombro,   D6)", PIN_BRAZO1, ANGULO_CAP_MIN, ANGULO_CAP_MAX, false, false};
  resultados[2] = {"BRAZO2 (muneca,  D10)", PIN_BRAZO2, ANGULO_CAP_MIN, ANGULO_CAP_MAX, false, false};

  servos[0] = &servoBase;
  servos[1] = &servoBrazo1;
  servos[2] = &servoBrazo2;

  Serial.println();
  Serial.println(F("=========================================="));
  Serial.println(F("  ENCONTRAR RANGOS SEGUROS POR SERVO"));
  Serial.println(F("=========================================="));
  Serial.println(F("Por cada servo:"));
  Serial.println(F("  1. Subo lento desde 90 -> manda algo cuando oigas zumbar."));
  Serial.println(F("  2. Bajo lento desde 90 -> manda algo cuando oigas zumbar."));
  Serial.println(F("Al final imprimo el resumen con los rangos."));
  Serial.println();
  delay(2500);

  for (int i = 0; i < N_SERVOS; i++) {
    calibrarServo(i);
  }

  imprimirResumen();
}

void loop() {
  // No hace nada — todo el trabajo va en setup().
  delay(1000);
}

void calibrarServo(int idx) {
  Resultado& r = resultados[idx];
  Servo& s = *servos[idx];

  Serial.println();
  Serial.print(F(">>> CALIBRANDO: "));
  Serial.println(r.nombre);

  apagarTodos();
  s.attach(r.pin);
  s.write(ANGULO_CENTRO);
  delay(1500);

  // ── Fase 1: SUBIR desde centro ──
  Serial.println(F("    Fase 1: SUBIENDO. Manda algo cuando zumbe."));
  vaciarSerial();
  int aFinal = ANGULO_CAP_MAX;
  for (int a = ANGULO_CENTRO + 1; a <= ANGULO_CAP_MAX; a++) {
    s.write(a);
    Serial.print(F("    angulo = "));
    Serial.println(a);
    if (Serial.available() > 0) {
      vaciarSerial();
      r.anguloMax = a;
      r.zumboSubiendo = true;
      aFinal = a;
      Serial.print(F("    [REGISTRADO MAX = "));
      Serial.print(a);
      Serial.println(F("]"));
      break;
    }
    delay(MS_POR_PASO);
  }
  if (!r.zumboSubiendo) {
    Serial.print(F("    [NO ZUMBO. Llego al cap "));
    Serial.print(ANGULO_CAP_MAX);
    Serial.println(F("]"));
  }

  // Volver al centro
  Serial.println(F("    Volviendo al centro..."));
  for (int a = aFinal; a >= ANGULO_CENTRO; a--) {
    s.write(a);
    delay(MS_POR_PASO / 2);
  }
  delay(1000);

  // ── Fase 2: BAJAR desde centro ──
  Serial.println(F("    Fase 2: BAJANDO. Manda algo cuando zumbe."));
  vaciarSerial();
  aFinal = ANGULO_CAP_MIN;
  for (int a = ANGULO_CENTRO - 1; a >= ANGULO_CAP_MIN; a--) {
    s.write(a);
    Serial.print(F("    angulo = "));
    Serial.println(a);
    if (Serial.available() > 0) {
      vaciarSerial();
      r.anguloMin = a;
      r.zumboBajando = true;
      aFinal = a;
      Serial.print(F("    [REGISTRADO MIN = "));
      Serial.print(a);
      Serial.println(F("]"));
      break;
    }
    delay(MS_POR_PASO);
  }
  if (!r.zumboBajando) {
    Serial.print(F("    [NO ZUMBO. Llego al cap "));
    Serial.print(ANGULO_CAP_MIN);
    Serial.println(F("]"));
  }

  // Volver al centro
  Serial.println(F("    Volviendo al centro..."));
  for (int a = aFinal; a <= ANGULO_CENTRO; a++) {
    s.write(a);
    delay(MS_POR_PASO / 2);
  }
  delay(1500);
  s.detach();
}

void apagarTodos() {
  servoBase.detach();
  servoBrazo1.detach();
  servoBrazo2.detach();
  servoPinza.detach();   // se queda apagada todo el rato
  delay(300);
}

void vaciarSerial() {
  while (Serial.available() > 0) Serial.read();
}

void imprimirResumen() {
  Serial.println();
  Serial.println();
  Serial.println(F("===================================================="));
  Serial.println(F("           RESUMEN: RANGOS SEGUROS POR SERVO"));
  Serial.println(F("===================================================="));
  Serial.println(F("Servo                    Pin   MIN    MAX    SEGURO"));
  Serial.println(F("------------------------------------------------------"));

  for (int i = 0; i < N_SERVOS; i++) {
    Resultado& r = resultados[i];

    int min_seg = r.zumboBajando  ? r.anguloMin + MARGEN_SEG : r.anguloMin;
    int max_seg = r.zumboSubiendo ? r.anguloMax - MARGEN_SEG : r.anguloMax;

    Serial.print(F("  "));
    Serial.print(r.nombre);
    Serial.print(F("  D"));
    Serial.print(r.pin);
    if (r.pin < 10) Serial.print(F(" "));
    Serial.print(F("  "));

    // MIN raw (con * si nunca zumbo)
    Serial.print(r.anguloMin);
    Serial.print(r.zumboBajando ? F(" ") : F("*"));
    Serial.print(F("   "));

    // MAX raw
    Serial.print(r.anguloMax);
    Serial.print(r.zumboSubiendo ? F(" ") : F("*"));
    Serial.print(F("   "));

    // Rango seguro
    Serial.print(min_seg);
    Serial.print(F("-"));
    Serial.println(max_seg);
  }

  Serial.println();
  Serial.println(F("(*)  El servo no zumbo en esa direccion: limite = cap del barrido."));
  Serial.print(F("SEGURO = MIN+"));
  Serial.print(MARGEN_SEG);
  Serial.print(F("  /  MAX-"));
  Serial.print(MARGEN_SEG);
  Serial.println(F("  (margen de seguridad)."));
  Serial.println();
  Serial.println(F("Copia los valores SEGURO a:"));
  Serial.println(F("  - config.py:  SERVO_*_MIN / SERVO_*_MAX"));
  Serial.println(F("  - brazo_robotico.ino:  *_MIN / *_MAX (BASE, BRAZO1, BRAZO2)"));
  Serial.println();
  Serial.println(F("=== FIN ==="));
}
