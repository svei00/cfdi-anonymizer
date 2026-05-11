"""Orquestador de alto nivel: procesa carpetas completas de CFDI.

Une catálogo de nombres + mapeo + fábrica de fakes + motor de enmascarado, y
coloca la salida plana o dentro de la estructura Bóveda. También expone el
modo revertir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from lxml import etree

from boveda import (CARPETA_BOVEDA_DEFAULT, EMITIDAS, RECIBIDAS,
                    clasificacion_de_ruta, es_rfc_valido, ruta_boveda)

from .fake_factory import FakeFactory
from .mapping_db import MappingDB
from .masking import MaskContext, cargar_y_enmascarar, escribir_arbol
from .nombres_db import NombresDB
from .revertir import construir_reverso, revertir_archivo, revertir_arbol

Progreso = Callable[[int, int, str], None]


@dataclass
class Resultado:
    total: int = 0
    exitosos: int = 0
    errores: list[tuple[str, str]] = field(default_factory=list)
    salidas: list[Path] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    detalle: list[str] = field(default_factory=list)
    carpetas: int = 0


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

    # ==================================================================
    # Modo Bóveda (espejo): refleja <RFC>/<Emitidas|Recibidas>/<yyyy>/<MM>
    # renombrando SÓLO la carpeta de RFC a su fake; conserva el resto.
    # ==================================================================
    @staticmethod
    def _detectar_carpetas_rfc(source_root: Path) -> list[Path]:
        """Devuelve las carpetas de RFC a procesar.

        Acepta dos formas de origen:
          1) la BÓVEDA raíz (con subcarpetas de RFC), o
          2) UNA carpeta de RFC (que contiene Emitidas/Recibidas adentro, o
             cuyo nombre ya es un RFC).
        """
        source_root = Path(source_root)
        subdirs = [p for p in source_root.iterdir() if p.is_dir()]
        sub_lower = {p.name.lower() for p in subdirs}
        es_carpeta_rfc = (EMITIDAS.lower() in sub_lower
                          or RECIBIDAS.lower() in sub_lower
                          or es_rfc_valido(source_root.name))
        if es_carpeta_rfc:
            return [source_root]
        return sorted(subdirs, key=lambda p: p.name)

    @staticmethod
    def _tag_de_clasif(clasif: str | None) -> str | None:
        if clasif == EMITIDAS:
            return "Emisor"
        if clasif == RECIBIDAS:
            return "Receptor"
        return None

    @staticmethod
    def _leer_tag(xml_path: Path, tag_local: str) -> tuple[str | None, str | None]:
        """Lee (Rfc, Nombre) de un hijo directo del Comprobante (Emisor/Receptor)."""
        try:
            root = etree.parse(str(xml_path)).getroot()
        except etree.XMLSyntaxError:
            return None, None
        for el in root:
            if isinstance(el.tag, str) and etree.QName(el).localname == tag_local:
                return el.get("Rfc"), el.get("Nombre")
        return None, None

    def _nombre_dueno(self, carpeta: Path, folder_rfc: str,
                      xmls: list[Path]) -> str | None:
        """Nombre del titular de la carpeta (desde el primer XML cuyo tag
        Emisor/Receptor coincide con el RFC de la carpeta)."""
        for xml in xmls:
            tag = self._tag_de_clasif(clasificacion_de_ruta(xml.relative_to(carpeta)))
            if not tag:
                continue
            rfc, nombre = self._leer_tag(xml, tag)
            if rfc and rfc.strip().upper() == folder_rfc:
                return nombre
        return None

    def procesar_boveda(self, source_root: Path | str,
                        dest_root: Path | str | None = None,
                        progreso: Progreso | None = None) -> Resultado:
        source_root = Path(source_root)
        dest_root = Path(dest_root) if dest_root else self.dest
        res = Resultado()

        # Reunir carpetas de RFC válidas y contar archivos (para el progreso).
        carpetas = self._detectar_carpetas_rfc(source_root)
        res.detalle.append(f"Origen: {source_root}")
        res.detalle.append(f"Destino: {dest_root}")
        res.detalle.append(f"Carpetas candidatas encontradas: {len(carpetas)}")
        plan: list[tuple[Path, list[Path]]] = []
        for d in carpetas:
            if not es_rfc_valido(d.name):
                res.avisos.append(f"Carpeta ignorada (no es un RFC): {d.name}")
                continue
            xmls = sorted(x for x in d.rglob("*.xml") if x.is_file())
            if not xmls:
                res.avisos.append(f"Carpeta de RFC sin XML: {d.name}")
                continue
            plan.append((d, xmls))
            res.total += len(xmls)

        if not plan:
            res.avisos.append(
                "No se encontraron carpetas de RFC con XML. Selecciona la Bóveda "
                "raíz (con subcarpetas de RFC) o una carpeta de RFC (que tenga "
                "Emitidas/Recibidas adentro).")

        hecho = 0
        for carpeta, xmls in plan:
            folder_rfc = carpeta.name.strip().upper()
            nombre = self._nombre_dueno(carpeta, folder_rfc, xmls)
            fake_folder = self.factory.entidad(folder_rfc, nombre or "").fake_rfc
            res.carpetas += 1
            res.detalle.append(
                f"RFC {folder_rfc} ({nombre or 'sin nombre'}) -> {fake_folder}"
                f"  [{len(xmls)} XML]")

            for xml in xmls:
                hecho += 1
                rel = xml.relative_to(carpeta)
                try:
                    clasif = clasificacion_de_ruta(rel)
                    tree, meta = cargar_y_enmascarar(xml, self.ctx)

                    # Validar que el tag dueño coincide con la carpeta.
                    if clasif == EMITIDAS:
                        real = meta.get("orig_emisor_rfc")
                    elif clasif == RECIBIDAS:
                        real = meta.get("orig_receptor_rfc")
                    else:
                        real = None
                        res.avisos.append(f"Sin Emitidas/Recibidas: {carpeta.name}/{rel}")
                    if real and real.strip().upper() != folder_rfc:
                        res.avisos.append(
                            f"Desubicado en {carpeta.name}/{rel}: "
                            f"tag={real} != carpeta={folder_rfc}")

                    out_path = dest_root / fake_folder / rel.parent / meta["nuevo_nombre"]
                    escribir_arbol(tree, out_path)
                    self.mapping.registrar_archivo(xml.name, meta["nuevo_nombre"], str(xml))
                    if not self.keep_originales:
                        xml.unlink()
                    res.salidas.append(out_path)
                    res.exitosos += 1
                except Exception as e:  # un archivo malo no detiene el lote
                    res.errores.append((f"{carpeta.name}/{rel}", f"{type(e).__name__}: {e}"))
                if progreso:
                    progreso(hecho, res.total, xml.name)
        return res

    def revertir_boveda(self, masked_root: Path | str, dest_root: Path | str,
                        progreso: Progreso | None = None) -> Resultado:
        """Revierte un espejo enmascarado a la estructura real (carpetas RFC
        reales y nombres de archivo originales)."""
        masked_root = Path(masked_root)
        dest_root = Path(dest_root)
        reverso = construir_reverso(self.mapping)
        res = Resultado()

        plan: list[tuple[Path, str, list[Path]]] = []
        for d in self._detectar_carpetas_rfc(masked_root):
            if not es_rfc_valido(d.name):
                res.avisos.append(f"Carpeta ignorada (no es un RFC): {d.name}")
                continue
            ent = self.mapping.buscar_entidad_por_fake(d.name.strip().upper())
            real_folder = ent.real_rfc if ent else d.name
            xmls = sorted(x for x in d.rglob("*.xml") if x.is_file())
            plan.append((d, real_folder, xmls))
            res.total += len(xmls)
            res.detalle.append(f"Fake {d.name} -> RFC {real_folder}  [{len(xmls)} XML]")

        hecho = 0
        for carpeta, real_folder, xmls in plan:
            res.carpetas += 1
            for xml in xmls:
                hecho += 1
                rel = xml.relative_to(carpeta)
                try:
                    tree = etree.parse(str(xml))
                    revertir_arbol(tree.getroot(), reverso)
                    fila = self.mapping.archivo_por_nuevo(xml.name)
                    nombre = fila["original_filename"] if fila else xml.name
                    escribir_arbol(tree, dest_root / real_folder / rel.parent / nombre)
                    res.exitosos += 1
                except Exception as e:
                    res.errores.append((f"{carpeta.name}/{rel}", f"{type(e).__name__}: {e}"))
                if progreso:
                    progreso(hecho, res.total, xml.name)
        return res

    def close(self):
        self.mapping.close()
        self.nombres.close()
