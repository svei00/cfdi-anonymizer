"""Homoclave.

Por ahora se genera una homoclave con FORMATO válido de forma aleatoria
(determinista si se pasa un objeto random sembrado). El algoritmo real
documentado por el SAT es una mejora opcional posterior; no se bloquea aquí.
"""

import random

# Conjunto de caracteres oficial de la homoclave del SAT.
_ALFABETO_HOMOCLAVE = "0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ"


def homoclave_aleatoria(rng: random.Random | None = None) -> str:
    """Tres caracteres con el alfabeto válido de homoclave."""
    rng = rng or random
    return "".join(rng.choice(_ALFABETO_HOMOCLAVE) for _ in range(3))
