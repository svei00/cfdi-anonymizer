"""Base de datos SQLite de nombres falsos (catálogo, sólo lectura en uso).

Crea y siembra las tablas:
    first_names(name, gender)
    last_names(surname)
    company_bases(base)
    regimenes(regimen, weight)
    schools(school)

Provee selección aleatoria (con `random.Random` opcional para reproducir).
"""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path

from . import seed_nombres

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "nombres.sqlite"


def construir(db_path: Path | str = DEFAULT_DB, *, sobrescribir: bool = False) -> Path:
    """Crea y siembra la base de nombres. Idempotente salvo `sobrescribir`."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists() and not sobrescribir:
        return db_path
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    try:
        con.executescript(
            """
            CREATE TABLE first_names (name TEXT NOT NULL, gender TEXT NOT NULL);
            CREATE TABLE last_names  (surname TEXT NOT NULL);
            CREATE TABLE company_bases(base TEXT NOT NULL);
            CREATE TABLE regimenes   (regimen TEXT NOT NULL, weight INTEGER NOT NULL);
            CREATE TABLE schools     (school TEXT NOT NULL);
            """
        )
        con.executemany("INSERT INTO first_names(name, gender) VALUES (?, ?)",
                        seed_nombres.FIRST_NAMES)
        con.executemany("INSERT INTO last_names(surname) VALUES (?)",
                        [(s,) for s in seed_nombres.LAST_NAMES])
        con.executemany("INSERT INTO company_bases(base) VALUES (?)",
                        [(b,) for b in seed_nombres.COMPANY_BASES])
        con.executemany("INSERT INTO regimenes(regimen, weight) VALUES (?, ?)",
                        seed_nombres.REGIMENES)
        con.executemany("INSERT INTO schools(school) VALUES (?)",
                        [(s,) for s in seed_nombres.SCHOOLS])
        con.commit()
    finally:
        con.close()
    return db_path


class NombresDB:
    """Acceso de sólo lectura al catálogo de nombres."""

    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = construir(db_path)  # asegura que exista
        self.con = sqlite3.connect(self.db_path)
        self._first = {
            "H": [r[0] for r in self.con.execute(
                "SELECT name FROM first_names WHERE gender='H'")],
            "M": [r[0] for r in self.con.execute(
                "SELECT name FROM first_names WHERE gender='M'")],
        }
        self._last = [r[0] for r in self.con.execute(
            "SELECT surname FROM last_names")]
        self._companies = [r[0] for r in self.con.execute(
            "SELECT base FROM company_bases")]
        self._regimenes = self.con.execute(
            "SELECT regimen, weight FROM regimenes").fetchall()
        self._schools = [r[0] for r in self.con.execute(
            "SELECT school FROM schools")]

    def nombre_pila(self, genero: str, rng: random.Random, *, dobles: bool = True) -> str:
        """1 o 2 nombres del género dado ('H'/'M')."""
        pool = self._first.get(genero.upper(), self._first["H"])
        n = 2 if (dobles and rng.random() < 0.4) else 1
        n = min(n, len(pool))
        return " ".join(rng.sample(pool, n))

    def apellido(self, rng: random.Random) -> str:
        return rng.choice(self._last)

    def dos_apellidos(self, rng: random.Random) -> tuple[str, str]:
        paterno = rng.choice(self._last)
        materno = rng.choice(self._last)
        return paterno, materno

    def regimen(self, rng: random.Random) -> str:
        regs, pesos = zip(*self._regimenes)
        return rng.choices(regs, weights=pesos, k=1)[0]

    def razon_social(self, rng: random.Random) -> str:
        base = rng.choice(self._companies)
        return f"{base}, {self.regimen(rng)}"

    def escuela(self, rng: random.Random) -> str:
        return rng.choice(self._schools)

    def close(self):
        self.con.close()
