"""Base de datos del mapeo real -> falso (consistencia + reversibilidad).

Persiste el mapeo real para poder REVERTIR (el modo revertir reproduce estas
tablas al revés). El sembrado (seed) da fakes reproducibles, pero el enmascarado
es de una sola vía: sin esta base no se puede revertir.

Tablas:
    entity_map(real_rfc UNIQUE, real_name, real_curp, tipo, fake_rfc UNIQUE,
               fake_name, fake_curp, fecha_iso)
    value_map(kind, real_value, fake_value)  UNIQUE(kind, real_value)
                                             UNIQUE(kind, fake_value)
    file_map(original_filename, new_filename, original_path)
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EntidadFalsa:
    real_rfc: str
    real_name: str
    real_curp: str | None
    tipo: str               # 'fisica' | 'moral'
    fake_rfc: str
    fake_name: str
    fake_curp: str | None
    fecha_iso: str          # nacimiento (física) o constitución (moral)
    # Sólo para personas físicas (None en morales). Permiten que un dependiente
    # (p. ej. alumno IEDU) comparta el apellido correcto con el padre/madre.
    genero: str | None = None          # 'H' | 'M'
    ap_paterno: str | None = None
    ap_materno: str | None = None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS entity_map (
    real_rfc  TEXT NOT NULL UNIQUE,
    real_name TEXT,
    real_curp TEXT,
    tipo      TEXT NOT NULL,
    fake_rfc  TEXT NOT NULL UNIQUE,
    fake_name TEXT NOT NULL,
    fake_curp TEXT,
    fecha_iso TEXT NOT NULL,
    genero    TEXT,
    ap_paterno TEXT,
    ap_materno TEXT
);
CREATE TABLE IF NOT EXISTS value_map (
    kind       TEXT NOT NULL,
    real_value TEXT NOT NULL,
    fake_value TEXT NOT NULL,
    UNIQUE(kind, real_value),
    UNIQUE(kind, fake_value)
);
CREATE TABLE IF NOT EXISTS file_map (
    original_filename TEXT NOT NULL,
    new_filename      TEXT NOT NULL,
    original_path     TEXT
);
"""


class MappingDB:
    """Acceso al mapeo persistente. Una instancia por corrida."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.db_path)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(_SCHEMA)
        self._migrar()
        self.con.commit()

    def _migrar(self) -> None:
        """Agrega columnas nuevas a una entity_map preexistente (compat)."""
        cols = {r[1] for r in self.con.execute("PRAGMA table_info(entity_map)")}
        for c in ("genero", "ap_paterno", "ap_materno"):
            if c not in cols:
                self.con.execute(f"ALTER TABLE entity_map ADD COLUMN {c} TEXT")

    # ---- entidades -----------------------------------------------------
    def buscar_entidad_por_real(self, real_rfc: str) -> EntidadFalsa | None:
        row = self.con.execute(
            "SELECT * FROM entity_map WHERE real_rfc=?", (real_rfc,)
        ).fetchone()
        return self._row_a_entidad(row) if row else None

    def buscar_entidad_por_fake(self, fake_rfc: str) -> EntidadFalsa | None:
        row = self.con.execute(
            "SELECT * FROM entity_map WHERE fake_rfc=?", (fake_rfc,)
        ).fetchone()
        return self._row_a_entidad(row) if row else None

    def fake_rfc_existe(self, fake_rfc: str) -> bool:
        return self.con.execute(
            "SELECT 1 FROM entity_map WHERE fake_rfc=?", (fake_rfc,)
        ).fetchone() is not None

    def insertar_entidad(self, e: EntidadFalsa) -> None:
        self.con.execute(
            "INSERT INTO entity_map(real_rfc, real_name, real_curp, tipo, "
            "fake_rfc, fake_name, fake_curp, fecha_iso, genero, ap_paterno, "
            "ap_materno) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (e.real_rfc, e.real_name, e.real_curp, e.tipo,
             e.fake_rfc, e.fake_name, e.fake_curp, e.fecha_iso,
             e.genero, e.ap_paterno, e.ap_materno),
        )
        self.con.commit()

    @staticmethod
    def _row_a_entidad(row: sqlite3.Row) -> EntidadFalsa:
        claves = row.keys()
        return EntidadFalsa(
            real_rfc=row["real_rfc"], real_name=row["real_name"],
            real_curp=row["real_curp"], tipo=row["tipo"],
            fake_rfc=row["fake_rfc"], fake_name=row["fake_name"],
            fake_curp=row["fake_curp"], fecha_iso=row["fecha_iso"],
            genero=row["genero"] if "genero" in claves else None,
            ap_paterno=row["ap_paterno"] if "ap_paterno" in claves else None,
            ap_materno=row["ap_materno"] if "ap_materno" in claves else None,
        )

    # ---- valores genéricos (CP, NSS, sellos, UUID, ...) ----------------
    def buscar_valor(self, kind: str, real_value: str) -> str | None:
        row = self.con.execute(
            "SELECT fake_value FROM value_map WHERE kind=? AND real_value=?",
            (kind, real_value),
        ).fetchone()
        return row["fake_value"] if row else None

    def buscar_valor_por_fake(self, kind: str, fake_value: str) -> str | None:
        row = self.con.execute(
            "SELECT real_value FROM value_map WHERE kind=? AND fake_value=?",
            (kind, fake_value),
        ).fetchone()
        return row["real_value"] if row else None

    def fake_valor_existe(self, kind: str, fake_value: str) -> bool:
        return self.con.execute(
            "SELECT 1 FROM value_map WHERE kind=? AND fake_value=?",
            (kind, fake_value),
        ).fetchone() is not None

    def insertar_valor(self, kind: str, real_value: str, fake_value: str) -> None:
        self.con.execute(
            "INSERT INTO value_map(kind, real_value, fake_value) VALUES (?,?,?)",
            (kind, real_value, fake_value),
        )
        self.con.commit()

    # ---- archivos ------------------------------------------------------
    def registrar_archivo(self, original_filename: str, new_filename: str,
                          original_path: str | None = None) -> None:
        self.con.execute(
            "INSERT INTO file_map(original_filename, new_filename, original_path) "
            "VALUES (?,?,?)",
            (original_filename, new_filename, original_path),
        )
        self.con.commit()

    def archivo_por_nuevo(self, new_filename: str) -> sqlite3.Row | None:
        return self.con.execute(
            "SELECT * FROM file_map WHERE new_filename=?", (new_filename,)
        ).fetchone()

    # ---- lecturas masivas (para revertir) ------------------------------
    def todas_entidades(self) -> list[sqlite3.Row]:
        return self.con.execute("SELECT * FROM entity_map").fetchall()

    def todos_valores(self) -> list[sqlite3.Row]:
        return self.con.execute(
            "SELECT kind, real_value, fake_value FROM value_map").fetchall()

    def close(self):
        self.con.close()
