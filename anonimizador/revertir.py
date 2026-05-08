"""Modo revertir: reconstruye los CFDI reales a partir del mapeo persistido.

El enmascarado es de una sola vía, pero como TODO reemplazo se guardó en
`MappingDB`, revertir es reproducir esas tablas al revés. Es genérico: recorre
todos los atributos del XML y, si su valor coincide con un fake conocido, lo
sustituye por el real. No necesita conocer cada handler -> escalable.

Nota: el Sello/Certificado se restauran al valor real guardado, así que un
archivo revertido vuelve a ser idéntico al original (salvo el nombre, que se
restaura desde file_map).
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from .mapping_db import MappingDB
from .masking.engine import escribir_arbol

_PARSER = etree.XMLParser(remove_blank_text=False, resolve_entities=False)


def construir_reverso(mapping: MappingDB) -> dict[str, str]:
    """Diccionario fake_value -> real_value de entidades y valores."""
    rev: dict[str, str] = {}
    for e in mapping.todas_entidades():
        rev[e["fake_rfc"]] = e["real_rfc"]
        if e["fake_name"] and e["real_name"]:
            rev[e["fake_name"]] = e["real_name"]
        if e["fake_curp"] and e["real_curp"]:
            rev[e["fake_curp"]] = e["real_curp"]
    for v in mapping.todos_valores():
        rev[v["fake_value"]] = v["real_value"]
    return rev


def revertir_arbol(root, reverso: dict[str, str]) -> int:
    """Sustituye en-sitio los valores fake por reales. Devuelve # cambios."""
    cambios = 0
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for attr, val in list(el.attrib.items()):
            real = reverso.get(val)
            if real is not None and real != val:
                el.set(attr, real)
                cambios += 1
    return cambios


def revertir_archivo(in_path: Path | str, out_dir: Path | str,
                     mapping: MappingDB,
                     reverso: dict[str, str] | None = None) -> Path:
    """Revierte un archivo enmascarado y lo escribe con su nombre original."""
    in_path = Path(in_path)
    reverso = reverso if reverso is not None else construir_reverso(mapping)

    tree = etree.parse(str(in_path), _PARSER)
    revertir_arbol(tree.getroot(), reverso)

    # Restaurar el nombre original desde file_map (si se conoce).
    fila = mapping.archivo_por_nuevo(in_path.name)
    nombre = fila["original_filename"] if fila else in_path.name
    return escribir_arbol(tree, Path(out_dir) / nombre)
