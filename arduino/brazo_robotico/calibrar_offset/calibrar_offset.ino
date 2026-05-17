/*
  calibrar_offset.ino  —  Encontrar OFFSET y SIGNO de cada servo

  Calibra la conversion:   servo = OFFSET + SIGNO * angulo_matematico

  Es un "jogger": mueve UN servo a la vez por Serial y muestra su valor.
  Los tres servos quedan enganchados y sosteniendo, asi el brazo no se
  desarma mientras calibras.

  ── COMO USARLO ───────────────────────────────────────────────
  1. Sube este sketch. Abre el Monitor Serial a 9600 baudios.
     IMPORTANTE: pon el final de linea en "Nueva linea" (Newline).
  2. Elige el servo:   b = base    1 = brazo1    2 = brazo2
  3. Muevelo:
        +       sube 1 grado          -       baja 1 grado
        +5      sube 5 (o +10, +N)    -5       baja 5 (o -N)
        95      va directo al angulo 95
        p       reimprime el estado
  4. Lleva el brazo a la POSE de referencia (abajo), anota el numero
     que muestra el Serial y mira hacia donde se movio.
  5. Pasale a Claude: numero anotado + direccion observada.

  ── POSES DE REFERENCIA ───────────────────────────────────────
  BASE   -> brazo apuntando RECTO HACIA ADELANTE (perpendicular al
            borde donde esta montada la base).  theta_rot = 90.
            Mira: al subir +, el brazo gira a tu izquierda o derecha?
  BRAZO1 -> primer eslabon (hombro -> codo) perfectamente HORIZONTAL
            (los dos ejes a la misma altura del piso).  theta1 = 0.
            Mira: al subir +, el eslabon SUBE o BAJA?
  BRAZO2 -> codo en ANGULO RECTO: el segundo eslabon a 90 grados del
            primero, formando una "L" (usa una escuadra).  |theta2| = 90.
            Mira: al subir +, el codo se ABRE (se endereza) o se
            CIERRA (se dobla mas)?

  ── SEGURIDAD ─────────────────────────────────────────────────
  Mueve de a poco. Si un servo ZUMBA, no sigas en esa direccion:
  esta contra un tope. RESET o desconecta el USB para parar.
*/

#include <Servo.h>

#define PIN_BASE   3
#define PIN_BRAZO1 6
#define PIN_BRAZO2 10

// Sin topes de software: rango completo del servo (0-180). Vos decidis
// hasta donde mover. OJO: si un servo ZUMBA es que llego a su tope
// mecanico; no insistas en esa direccion o se recalienta.
const int BASE_MIN  = 0,   BASE_MAX  = 180;
const int BRAZO_MIN = 0,   BRAZO_MAX = 180;

// Valores iniciales: brazo arranca quieto y estable.
const int INICIO_BASE   = 90;
const int INICIO_BRAZO1 = 90;
const int INICIO_BRAZO2 = 90;

Servo servoBase, servoBrazo1, servoBrazo2;

int angBase   = INICIO_BASE;
int angBrazo1 = INICIO_BRAZO1;
int angBrazo2 = INICIO_BRAZO2;

char sel = '1';        // servo seleccionado: 'b', '1' o '2'
String linea = "";

void setup() {
  Serial.begin(9600);
  delay(300);

  servoBase.attach(PIN_BASE);
  servoBrazo1.attach(PIN_BRAZO1);
  servoBrazo2.attach(PIN_BRAZO2);

  servoBase.write(angBase);
  servoBrazo1.write(angBrazo1);
  servoBrazo2.write(angBrazo2);
  delay(600);

  Serial.println();
  Serial.println(F("=== CALIBRAR OFFSET ==="));
  imprimirAyuda();
  imprimirEstado();
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      procesar(linea);
      linea = "";
    } else if (c != ' ') {
      linea += c;
    }
  }
}

void procesar(String s) {
  if (s.length() == 0) return;

  if (s == "b" || s == "1" || s == "2") {
    sel = s[0];
    Serial.print(F(">> Servo seleccionado: "));
    Serial.println(nombreSel());
    imprimirEstado();
    return;
  }
  if (s == "p") { imprimirEstado(); return; }
  if (s == "h" || s == "?") { imprimirAyuda(); return; }

  int *ang;
  int lo, hi;
  servoActual(&ang, &lo, &hi);

  int objetivo = *ang;
  char c0 = s[0];

  if (c0 == '+' || c0 == '-') {
    int paso = (s.length() > 1) ? s.substring(1).toInt() : 1;
    if (paso == 0) paso = 1;
    objetivo = *ang + (c0 == '+' ? paso : -paso);
  } else if (esNumero(s)) {
    objetivo = s.toInt();
  } else {
    Serial.print(F(">> Comando desconocido: "));
    Serial.println(s);
    return;
  }

  int objClamp = constrain(objetivo, lo, hi);
  if (objClamp != objetivo) {
    Serial.print(F(">> Limite alcanzado, recortado a "));
    Serial.println(objClamp);
  }
  moverSuave(ang, objClamp);
  imprimirEstado();
}

bool esNumero(String s) {
  for (unsigned int i = 0; i < s.length(); i++) {
    if (!isDigit(s[i])) return false;
  }
  return s.length() > 0;
}

void servoActual(int **ang, int *lo, int *hi) {
  if (sel == 'b')      { *ang = &angBase;   *lo = BASE_MIN;  *hi = BASE_MAX;  }
  else if (sel == '1') { *ang = &angBrazo1; *lo = BRAZO_MIN; *hi = BRAZO_MAX; }
  else                 { *ang = &angBrazo2; *lo = BRAZO_MIN; *hi = BRAZO_MAX; }
}

Servo& servoObj() {
  if (sel == 'b') return servoBase;
  if (sel == '1') return servoBrazo1;
  return servoBrazo2;
}

void moverSuave(int *ang, int objetivo) {
  Servo &s = servoObj();
  while (*ang != objetivo) {
    *ang += (*ang < objetivo) ? 1 : -1;
    s.write(*ang);
    delay(15);
  }
}

const __FlashStringHelper* nombreSel() {
  if (sel == 'b') return F("BASE");
  if (sel == '1') return F("BRAZO1");
  return F("BRAZO2");
}

void imprimirAyuda() {
  Serial.println(F("Comandos:  b/1/2 elegir servo | + - mueve 1 | +N -N mueve N"));
  Serial.println(F("           N va al angulo N | p estado | h ayuda"));
}

void imprimirEstado() {
  Serial.print(F(">> ["));
  Serial.print(nombreSel());
  Serial.print(F("]  base="));
  Serial.print(angBase);
  Serial.print(F("  brazo1="));
  Serial.print(angBrazo1);
  Serial.print(F("  brazo2="));
  Serial.println(angBrazo2);
}
