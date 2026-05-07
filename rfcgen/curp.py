"""Generación de CURP (18 caracteres).

 1-4 : letras (igual criterio que RFC física, con censura de inconvenientes)
 5-10: AAMMDD de nacimiento
 11  : sexo (H/M)
 12-13: clave de entidad federativa (2 letras)
 14  : primera consonante interna del apellido paterno
 15  : primera consonante interna del apellido materno
 16  : primera consonante interna del nombre
 17  : homoclave de diferenciación (0-9 nacidos <2000, A-Z nacidos >=2000)
 18  : dígito verificador (0-9)
"""

import random
from datetime import date

from . import _texto
from .entidades import CLAVES_ENTIDAD
from .palabras import censurar_si_inconveniente

_DICCIONARIO_VERIF = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"


def letras_curp(nombre: str, apellido_paterno: str,
                apellido_materno: str) -> str:
    pat = _texto.palabras_significativas(apellido_paterno)
    pat = pat[0] if pat else "X"
    mat = _texto.palabras_significativas(apellido_materno)
    mat = mat[0] if mat else "X"
    nom = _texto.primer_nombre_util(nombre) or "X"

    letras = (
        pat[0]
        + _texto.primera_vocal_interna(pat)
        + (mat[0] if mat else "X")
        + (nom[0] if nom else "X")
    )
    letras = (letras + "XXXX")[:4]
    return censurar_si_inconveniente(letras)


def _digito_verificador(curp17: str) -> str:
    """Algoritmo oficial del dígito verificador de la CURP."""
    suma = 0
    for i, c in enumerate(curp17):
        valor = _DICCIONARIO_VERIF.find(c)
        if valor < 0:
            valor = 0
        suma += valor * (18 - i)
    digito = (10 - (suma % 10)) % 10
    return str(digito)


def curp(nombre: str, apellido_paterno: str, apellido_materno: str,
         fecha_nac: date, sexo: str,
         clave_entidad: str | None = None,
         rng: random.Random | None = None) -> str:
    """Genera una CURP. ``sexo`` es 'H' o 'M'."""
    rng = rng or random
    sexo = sexo.upper()[:1]
    if sexo not in ("H", "M"):
        sexo = rng.choice(("H", "M"))
    clave_entidad = clave_entidad or rng.choice(CLAVES_ENTIDAD)

    letras = letras_curp(nombre, apellido_paterno, apellido_materno)
    fecha_txt = fecha_nac.strftime("%y%m%d")

    pat = _texto.palabras_significativas(apellido_paterno)
    pat = pat[0] if pat else "X"
    mat = _texto.palabras_significativas(apellido_materno)
    mat = mat[0] if mat else "X"
    nom = _texto.primer_nombre_util(nombre) or "X"

    consonantes = (
        _texto.primera_consonante_interna(pat)
        + _texto.primera_consonante_interna(mat)
        + _texto.primera_consonante_interna(nom)
    )

    # Posición 17: homoclave de diferenciación según siglo de nacimiento.
    if fecha_nac.year < 2000:
        dif = str(rng.randint(0, 9))
    else:
        dif = rng.choice("ABCDEFGHIJKLMNPQRSTUVWXYZ")

    curp17 = f"{letras}{fecha_txt}{sexo}{clave_entidad}{consonantes}{dif}"
    return curp17 + _digito_verificador(curp17)
