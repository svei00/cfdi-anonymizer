"""Orquestador de alto nivel: procesa carpetas completas de CFDI.

Une catálogo de nombres + mapeo + fábrica de fakes + motor de enmascarado, y
coloca la salida plana o dentro de la estructura Bóveda. También expone el
modo revertir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from boveda import CARPETA_BOVEDA_DEFAULT, EMITIDAS, ruta_boveda

from .fake_factory import FakeFactory
from .mapping_db import MappingDB
from .masking import MaskContext, cargar_y_enmascarar, escribir_arbol
from .nombres_db import NombresDB
from .revertir import construir_reverso, revertir_archivo

Progreso = Callable[[int, int, str], None]


@dataclass
class Resultado:
    total: int = 0
    exitosos: int = 0
    errores: list[tuple[str, str]] = field(default_factory=list)
    salidas: list[Path] = field(default_factory=list)


class Procesador:
    def __init__(self, dest_dir: Path | str, *, db_dir: Path | str | None = None,
                 seed: int | None = None, jitter_salarios: bool = False,
                 usar_boveda: bool = False, app_name: str = "CFDI Anonymizer",
                 carpeta_boveda: str = CARPETA_BOVEDA_DEFAULT,
                 keep_originales: bool = True,
                 nombres_db_path: Path | str | None = None):
        self.dest = Path(dest_dir)
        self.dest.mkdir(parents=True, exist_ok=True)
        carpeta_db = Path(db_dir) if db_dir else self.dest
        self.mapping = MappingDB(carpeta_db / "mapeo.sqlite")
        self.nombres = (NombresDB(nombres_db_path) if nombres_db_path
                        else NombresDB())
        self.factory = FakeFactory(self.nombres, self.mapping, seed=seed)
        self.ctx = MaskContext(self.factory, jitter_salarios=jitter_salarios)
        self.usar_boveda = usar_boveda
        self.app_name = app_name
        self.carpeta_boveda = carpeta_boveda
        self.keep_originales = keep_originales

    # ------------------------------------------------------------------
    def _destino_dir(self, meta: dict) -> Path:
        if self.usar_boveda and meta.get("emisor_rfc"):
            return ruta_boveda(self.dest, self.app_name, meta["emisor_rfc"],
                               EMITIDAS, meta["fecha"],
                               carpeta_boveda=self.carpeta_boveda, crear=True)
        return self.dest

    def procesar_archivo(self, path: Path | str) -> Path:
        path = Path(path)
        tree, meta = cargar_y_enmascarar(path, self.ctx)
        out_dir = self._destino_dir(meta)
        out_path = out_dir / meta["nuevo_nombre"]
        escribir_arbol(tree, out_path)
        self.mapping.registrar_archivo(path.name, meta["nuevo_nombre"], str(path))
        if not self.keep_originales:
            path.unlink()
        return out_path

    def _listar_xml(self, source_dir: Path | str) -> list[Path]:
        return sorted(p for p in Path(source_dir).rglob("*.xml") if p.is_file())

    def procesar_carpeta(self, source_dir: Path | str,
                         progreso: Progreso | None = None) -> Resultado:
        archivos = self._listar_xml(source_dir)
        res = Resultado(total=len(archivos))
        for i, x in enumerate(archivos, 1):
            try:
                res.salidas.append(self.procesar_archivo(x))
                res.exitosos += 1
            except Exception as e:  # un archivo malo no detiene el lote
                res.errores.append((x.name, f"{type(e).__name__}: {e}"))
            if progreso:
                progreso(i, len(archivos), x.name)
        return res

    # ------------------------------------------------------------------
    def revertir_carpeta(self, source_dir: Path | str, out_dir: Path | str,
                         progreso: Progreso | None = None) -> Resultado:
        archivos = self._listar_xml(source_dir)
        reverso = construir_reverso(self.mapping)
        res = Resultado(total=len(archivos))
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, x in enumerate(archivos, 1):
            try:
                revertir_archivo(x, out_dir, self.mapping, reverso)
                res.exitosos += 1
            except Exception as e:
                res.errores.append((x.name, f"{type(e).__name__}: {e}"))
            if progreso:
                progreso(i, len(archivos), x.name)
        return res

    def close(self):
        self.mapping.close()
        self.nombres.close()
