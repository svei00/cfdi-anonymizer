"""rfcgen — generador reutilizable de RFC y CURP mexicanos.

Módulo independiente y sin dependencias externas, pensado para reutilizarse
tanto en el anonimizador de CFDI como en la app principal de CFDI.

API pública:
    rfc_fisica(nombre, ap_paterno, ap_materno, fecha_nac, rng=None) -> str
    rfc_moral(razon_social, fecha_constitucion, rng=None) -> str
    curp(nombre, ap_paterno, ap_materno, fecha_nac, sexo, clave_entidad=None,
         rng=None) -> str
"""

from .curp import curp, letras_curp
from .entidades import CLAVES_ENTIDAD, ENTIDADES
from .homoclave import homoclave_aleatoria
from .rfc import letras_rfc_fisica, letras_rfc_moral, rfc_fisica, rfc_moral

__all__ = [
    "rfc_fisica",
    "rfc_moral",
    "curp",
    "letras_rfc_fisica",
    "letras_rfc_moral",
    "letras_curp",
    "homoclave_aleatoria",
    "ENTIDADES",
    "CLAVES_ENTIDAD",
]
