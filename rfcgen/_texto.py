"""Utilidades de normalización de texto para RFC y CURP.

Implementa las reglas de limpieza del SAT/RENAPO: acentos, la Ñ, los
caracteres especiales y las palabras que se ignoran (artículos,
preposiciones, conjunciones y régimen de capital).
"""

import unicodedata

VOCALES = set("AEIOU")

# Tokens que forman parte de un régimen de capital. Tras normalizar, los
# puntos se vuelven espacios, así que "S.A. de C.V." -> "S A DE C V". Se
# eliminan estos tokens del FINAL de la razón social antes de tomar las
# iniciales del RFC moral.
_TOKENS_REGIMEN = {
    "S", "A", "B", "C", "V", "R", "L", "P", "I", "N", "E", "DE", "EN",
    "SA", "CV", "SC", "SAB", "SAPI", "SRL", "RL", "SNC", "AC", "SCS", "SCA",
}

# Palabras que NO cuentan al tomar iniciales (apellidos compuestos y razón
# social). Se comparan en mayúsculas y sin acentos.
PALABRAS_IGNORADAS = {
    "DE", "LA", "LAS", "LOS", "EL", "Y", "DEL", "MC", "MAC", "VON", "VAN",
    "COMPANIA", "CIA", "SOCIEDAD", "SOC", "EN", "DERL",
    # Régimen de capital y abreviaturas mercantiles
    "SA", "DE", "CV", "SC", "SAB", "SRL", "SAPI", "SOFOM", "ENR", "SNC",
    "SCS", "SCA", "AC",
}

# Nombres de pila que se ignoran cuando hay un segundo nombre (regla del
# "primer nombre" para RFC/CURP de persona física).
NOMBRES_COMUNES = {"JOSE", "MARIA", "J", "MA", "MA.", "J.", "JOSE MARIA"}


def normalizar(texto: str) -> str:
    """Mayúsculas, sin acentos, Ñ -> N, sólo letras y espacios."""
    if not texto:
        return ""
    # Descomponer acentos y quitarlos; la Ñ se trata aparte.
    texto = texto.replace("ñ", "N#").replace("Ñ", "N#")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("N#", "N")
    texto = texto.upper()
    # Conservar sólo letras y espacios
    limpio = []
    for c in texto:
        if c.isalpha() or c == " ":
            limpio.append(c)
        else:
            limpio.append(" ")
    return " ".join("".join(limpio).split())


def quitar_regimen(razon_social: str) -> str:
    """Elimina el régimen de capital del final de una razón social.

    Trabaja sobre la forma normalizada y descarta tokens de régimen desde el
    final mientras lo sean, deteniéndose en la primera palabra real.
    """
    tokens = normalizar(razon_social).split()
    while len(tokens) > 1 and tokens[-1] in _TOKENS_REGIMEN:
        tokens.pop()
    return " ".join(tokens)


def palabras_significativas(texto: str) -> list[str]:
    """Divide en palabras ignorando artículos/preposiciones/régimen."""
    palabras = normalizar(texto).split()
    sig = [p for p in palabras if p not in PALABRAS_IGNORADAS]
    return sig or palabras  # nunca devolver lista vacía


def primer_nombre_util(nombre: str) -> str:
    """Devuelve el nombre de pila que cuenta para las iniciales.

    Si el primer nombre es común (José, María, J, Ma) y hay otro, usa el
    segundo.
    """
    partes = normalizar(nombre).split()
    if not partes:
        return ""
    if partes[0] in NOMBRES_COMUNES and len(partes) > 1:
        return partes[1]
    return partes[0]


def primera_vocal_interna(palabra: str) -> str:
    """Primera vocal de la palabra a partir de la segunda letra."""
    for c in palabra[1:]:
        if c in VOCALES:
            return c
    return "X"


def primera_consonante_interna(palabra: str) -> str:
    """Primera consonante de la palabra a partir de la segunda letra."""
    for c in palabra[1:]:
        if c.isalpha() and c not in VOCALES:
            return c
    return "X"
