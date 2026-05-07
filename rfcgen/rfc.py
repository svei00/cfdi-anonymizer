"""Generación de RFC (persona física y moral).

Persona física  (13): 4 letras + AAMMDD + homoclave(3)
Persona moral   (12): 3 letras + AAMMDD + homoclave(3)

Las letras siguen las reglas del SAT (vocal interna, palabras inconvenientes,
artículos ignorados). La homoclave es de formato válido aleatorio.
"""

import random
from datetime import date

from . import _texto
from .homoclave import homoclave_aleatoria
from .palabras import censurar_si_inconveniente


def _fecha_aammdd(fecha: date) -> str:
    return fecha.strftime("%y%m%d")


def letras_rfc_fisica(nombre: str, apellido_paterno: str,
                      apellido_materno: str = "") -> str:
    """Cuatro letras iniciales del RFC de persona física."""
    pat = _texto.palabras_significativas(apellido_paterno)
    pat = pat[0] if pat else ""
    mat = _texto.palabras_significativas(apellido_materno)
    mat = mat[0] if mat else ""
    nom = _texto.primer_nombre_util(nombre)

    if pat and len(pat) >= 2 and mat:
        # Caso normal: inicial + vocal interna del paterno, inicial materno,
        # inicial nombre.
        letras = (
            pat[0]
            + _texto.primera_vocal_interna(pat)
            + (mat[0] if mat else "X")
            + (nom[0] if nom else "X")
        )
    elif pat and mat:
        # Apellido paterno de una sola letra.
        letras = (pat[0] + mat[0] + (nom[:2].ljust(2, "X")))[:4]
    elif pat and not mat:
        # Sin apellido materno: dos primeras del paterno + dos del nombre.
        letras = (pat[:2].ljust(2, "X") + (nom[:2].ljust(2, "X")))[:4]
    else:
        letras = (nom[:4]).ljust(4, "X")

    letras = (letras + "XXXX")[:4]
    return censurar_si_inconveniente(letras)


def letras_rfc_moral(razon_social: str) -> str:
    """Tres letras iniciales del RFC de persona moral."""
    razon_social = _texto.quitar_regimen(razon_social)
    palabras = _texto.palabras_significativas(razon_social)
    iniciales = ""
    for p in palabras:
        iniciales += p[0]
        if len(iniciales) == 3:
            break
    if len(iniciales) < 3 and palabras:
        # Completar con las siguientes letras de la primera palabra.
        iniciales = (iniciales + palabras[0][1:])[:3]
    return (iniciales + "XXX")[:3]


def rfc_fisica(nombre: str, apellido_paterno: str, apellido_materno: str,
               fecha_nac: date, rng: random.Random | None = None) -> str:
    letras = letras_rfc_fisica(nombre, apellido_paterno, apellido_materno)
    return f"{letras}{_fecha_aammdd(fecha_nac)}{homoclave_aleatoria(rng)}"


def rfc_moral(razon_social: str, fecha_constitucion: date,
              rng: random.Random | None = None) -> str:
    letras = letras_rfc_moral(razon_social)
    return f"{letras}{_fecha_aammdd(fecha_constitucion)}{homoclave_aleatoria(rng)}"
