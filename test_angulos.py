from brazo_robotico.sistema import SistemaBrazo

s = SistemaBrazo()
casillas = ['A1', 'A8', 'D4', 'E4', 'H1', 'H8', 'B1', 'C3']

print(f"{'Casilla':>8} | {'Servo Base':>10} | {'Servo Brazo1':>12} | {'Servo Brazo2':>12}")
print("-" * 55)
for c in casillas:
    coord = s.casilla_a_xyz(c)
    ang = s.calcular_angulos(coord.x, coord.y)
    sv = s.angulos_a_servos(ang)
    print(f"{c:>8} | {sv.base:>10.1f} | {sv.brazo1:>12.1f} | {sv.brazo2:>12.1f}")
