"""boveda — estructura de carpetas de almacenamiento de CFDI (reutilizable).

Estructura:
    <raiz>/<AppName>/<Boveda>/<RFC>/<Emitidas|Recibidas>/<YYYY>/<MM>/

La clasificación Emitidas/Recibidas se determina según si el RFC objetivo
(el "dueño" de la bóveda) es el Emisor o el Receptor del comprobante.

Módulo independiente, sin dependencias externas; pensado para reutilizarse en
la app principal de CFDI.
"""

from .estructura import (CARPETA_BOVEDA_DEFAULT, EMITIDAS, RECIBIDAS,
                         anio_mes_de_fecha, clasificacion, ruta_boveda,
                         ruta_relativa)

__all__ = [
    "EMITIDAS", "RECIBIDAS", "CARPETA_BOVEDA_DEFAULT",
    "clasificacion", "ruta_relativa", "ruta_boveda", "anio_mes_de_fecha",
]
