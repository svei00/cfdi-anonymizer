"""Infraestructura común del motor de enmascarado.

Define:
  - Espacios de nombres (namespaces) conocidos del SAT.
  - `MaskContext`: fábrica de fakes + opciones, con atajos para enmascarar
    atributos respetando la consistencia.
  - `Handler` base y el `REGISTRO` ordenado de handlers.
  - Utilidades para encontrar elementos por nombre local (robusto entre
    versiones de CFDI) y namespace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from lxml import etree

from ..fake_factory import FakeFactory

# --- Namespaces conocidos -------------------------------------------------
NS_CFDI_PREFIX = "http://www.sat.gob.mx/cfd/"          # /cfd/3, /cfd/4, futuros
NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"
NS_NOMINA12 = "http://www.sat.gob.mx/nomina12"
NS_PAGOS20 = "http://www.sat.gob.mx/Pagos20"
NS_PAGOS10 = "http://www.sat.gob.mx/Pagos"
NS_IEDU = "http://www.sat.gob.mx/iedu"


# --- Utilidades de árbol --------------------------------------------------
def qname(el) -> etree.QName:
    return etree.QName(el)


def localname(el) -> str:
    return etree.QName(el).localname


def namespace_de(el) -> str:
    return etree.QName(el).namespace or ""


def cfdi_namespace(root) -> str | None:
    """Namespace CFDI del documento (cfd/3, cfd/4 o futuros)."""
    ns = namespace_de(root)
    return ns if ns.startswith(NS_CFDI_PREFIX) else None


def cfdi_version(root) -> str:
    """Versión del CFDI a partir del namespace, p. ej. '4'."""
    ns = cfdi_namespace(root) or ""
    return ns[len(NS_CFDI_PREFIX):] if ns else ""


def buscar(root, local: str, namespace: str | None = None) -> list:
    """Todos los elementos con ese nombre local (y namespace opcional)."""
    out = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue  # comentarios / PIs
        q = etree.QName(el)
        if q.localname == local and (namespace is None or q.namespace == namespace):
            out.append(el)
    return out


def hijos_directos(parent, local: str) -> list:
    return [el for el in parent if isinstance(el.tag, str)
            and etree.QName(el).localname == local]


def namespace_presente(root, namespace: str) -> bool:
    for el in root.iter():
        if isinstance(el.tag, str) and etree.QName(el).namespace == namespace:
            return True
    return False


# --- Contexto de enmascarado ---------------------------------------------
@dataclass
class MaskContext:
    factory: FakeFactory
    jitter_salarios: bool = False
    # Entidades enmascaradas en este documento (las fija el handler base para
    # que los complementos -Nómina, IEDU- aten datos al mismo fake).
    emisor_entidad: object = None
    receptor_entidad: object = None
    # Reporte simple de lo que se tocó (para log/depuración).
    contadores: dict = field(default_factory=dict)

    def _conteo(self, clave: str) -> None:
        self.contadores[clave] = self.contadores.get(clave, 0) + 1

    def remap_attr(self, el, attr: str, func: Callable[[str], str],
                   etiqueta: str | None = None) -> None:
        """Reemplaza un atributo (si existe y no está vacío) usando func."""
        val = el.get(attr)
        if val:
            el.set(attr, func(val))
            self._conteo(etiqueta or attr)

    def rfc(self, real: str) -> str:
        """RFC falso consistente (respeta RFC genéricos passthrough)."""
        return self.factory.entidad(real).fake_rfc


# --- Registro de handlers -------------------------------------------------
class Handler:
    """Clase base de un handler de complemento."""

    nombre = "base"

    def aplica(self, root) -> bool:  # pragma: no cover - override
        raise NotImplementedError

    def enmascarar(self, root, ctx: MaskContext) -> None:  # pragma: no cover
        raise NotImplementedError


REGISTRO: list[Handler] = []


def registrar(handler_cls):
    """Decorador para registrar un handler (orden = orden de import)."""
    REGISTRO.append(handler_cls())
    return handler_cls
