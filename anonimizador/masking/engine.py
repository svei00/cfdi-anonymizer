"""Orquestador: parsea un CFDI, corre los handlers y escribe el mock.

El archivo resultante NO será válido para el SAT (el Sello no coincide) pero
SÍ debe parsear. Se renombra usando el UUID falso (si hay TFD) para imitar el
nombrado real, y se registra el mapeo de archivo para poder revertir.
"""

from __future__ import annotations

import uuid as _uuid
from pathlib import Path

from lxml import etree

from .base import NS_TFD, REGISTRO, MaskContext, buscar, hijos_directos

_PARSER = etree.XMLParser(remove_blank_text=False, resolve_entities=False)


def enmascarar_arbol(root, ctx: MaskContext) -> None:
    """Aplica, en orden, todos los handlers que apliquen al documento."""
    for handler in REGISTRO:
        if handler.aplica(root):
            handler.enmascarar(root, ctx)


def _uuid_falso(root) -> str | None:
    tfds = buscar(root, "TimbreFiscalDigital", NS_TFD)
    if tfds and tfds[0].get("UUID"):
        return tfds[0].get("UUID")
    return None


def _attr_primer_hijo(root, local: str, attr: str) -> str | None:
    hijos = hijos_directos(root, local)
    return hijos[0].get(attr) if hijos else None


def cargar_y_enmascarar(in_path: Path | str, ctx: MaskContext):
    """Parsea y enmascara; devuelve (tree, meta) SIN escribir.

    `meta` lleva los datos YA enmascarados útiles para nombrar/archivar:
    emisor_rfc, receptor_rfc, fecha, uuid, nuevo_nombre.
    """
    tree = etree.parse(str(in_path), _PARSER)
    root = tree.getroot()
    # Reiniciar el estado por-documento (evita arrastrar entidades de otro
    # archivo cuando se reutiliza el mismo contexto en lote).
    ctx.emisor_entidad = None
    ctx.receptor_entidad = None
    enmascarar_arbol(root, ctx)

    nuevo_uuid = _uuid_falso(root)
    meta = {
        "emisor_rfc": _attr_primer_hijo(root, "Emisor", "Rfc"),
        "receptor_rfc": _attr_primer_hijo(root, "Receptor", "Rfc"),
        "fecha": root.get("Fecha", ""),
        "uuid": nuevo_uuid,
        "nuevo_nombre": f"{(nuevo_uuid or str(_uuid.uuid4()).upper())}.xml",
    }
    return tree, meta


def escribir_arbol(tree, out_path: Path | str) -> Path:
    """Escribe el árbol conservando declaración/encoding del original."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Sólo conservar standalone si el documento original lo declaró (los
    # CFDI normalmente NO lo declaran).
    standalone = tree.docinfo.standalone if tree.docinfo.standalone else None
    tree.write(
        str(out_path),
        xml_declaration=True,
        encoding=tree.docinfo.encoding or "UTF-8",
        standalone=standalone,
    )
    return out_path


def enmascarar_archivo(in_path: Path | str, out_dir: Path | str,
                       ctx: MaskContext, *, registrar_archivo: bool = True) -> Path:
    """Enmascara un archivo CFDI hacia `out_dir` (plano) y devuelve la ruta."""
    in_path = Path(in_path)
    tree, meta = cargar_y_enmascarar(in_path, ctx)
    out_path = Path(out_dir) / meta["nuevo_nombre"]
    escribir_arbol(tree, out_path)
    if registrar_archivo:
        ctx.factory.mapping.registrar_archivo(
            in_path.name, meta["nuevo_nombre"], str(in_path))
    return out_path
