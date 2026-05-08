"""Motor de enmascarado por manejadores (handlers) por complemento.

Diseño escalable: cada complemento (Nómina, Pagos, IEDU, futuros) es un
handler independiente registrado en `REGISTRO`. Agregar un caso nuevo es
agregar un handler — no tocar una lista plana.
"""

from .base import REGISTRO, Handler, MaskContext, registrar
from .engine import (cargar_y_enmascarar, enmascarar_archivo, enmascarar_arbol,
                     escribir_arbol)

# Importar los handlers registra sus clases (efecto de import).
from . import handler_cfdi, handler_tfd, handler_nomina, handler_pagos, handler_iedu  # noqa: E402,F401

__all__ = [
    "REGISTRO", "Handler", "MaskContext", "registrar",
    "enmascarar_archivo", "enmascarar_arbol", "cargar_y_enmascarar",
    "escribir_arbol",
]
