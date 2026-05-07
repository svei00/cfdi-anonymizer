"""Demostración runnable:  python -m rfcgen"""

import random
from datetime import date

from . import curp, rfc_fisica, rfc_moral
from .entidades import ENTIDADES

rng = random.Random(42)  # semilla fija -> salida reproducible


def _demo_fisica(nombre, pat, mat, fecha, sexo):
    r = rfc_fisica(nombre, pat, mat, fecha, rng)
    c = curp(nombre, pat, mat, fecha, sexo, rng=rng)
    print(f"  {nombre} {pat} {mat}")
    print(f"    RFC : {r}   ({len(r)} chars)")
    print(f"    CURP: {c}   ({len(c)} chars)")


def _demo_moral(razon, fecha):
    r = rfc_moral(razon, fecha, rng)
    print(f"  {razon}")
    print(f"    RFC : {r}   ({len(r)} chars)")


def main():
    print("== Personas físicas ==")
    _demo_fisica("Juan", "Pérez", "García", date(1985, 3, 12), "H")
    _demo_fisica("María Guadalupe", "Hernández", "López", date(1990, 11, 5), "M")
    _demo_fisica("José Antonio", "Müller", "Náñez", date(2001, 7, 28), "H")
    _demo_fisica("Ana", "Buendía", "Yáñez", date(1972, 1, 3), "M")  # censura

    print("\n== Personas morales ==")
    _demo_moral("Ferreterías Calzada, S.A. de C.V.", date(2003, 6, 1))
    _demo_moral("Sal Si Puedes, S.C.", date(2010, 9, 15))
    _demo_moral("Tacos El Mareado, S.A. de R.L. de C.V.", date(1998, 2, 20))

    print(f"\n({len(ENTIDADES)} claves de entidad cargadas)")


if __name__ == "__main__":
    main()
