"""Palabras altisonantes / inconvenientes.

El SAT y RENAPO sustituyen la cuarta letra del RFC (o la segunda letra de la
CURP) por una 'X' cuando las cuatro letras iniciales forman una palabra
considerada obscena o inconveniente. Esta es la lista publicada en el
Anexo del Diario Oficial de la Federación.
"""

PALABRAS_INCONVENIENTES = {
    "BUEI", "BUEY", "CACA", "CACO", "CAGA", "CAGO", "CAKA", "CAKO",
    "COGE", "COGI", "COJA", "COJE", "COJI", "COJO", "COLA", "CULO",
    "FALO", "FETO", "GETA", "GUEI", "GUEY", "JETA", "JOTO", "KACA",
    "KACO", "KAGA", "KAGO", "KAKA", "KAKO", "KOGE", "KOGI", "KOJA",
    "KOJE", "KOJI", "KOJO", "KOLA", "KULO", "LILO", "LOCA", "LOCO",
    "LOKA", "LOKO", "MAME", "MAMO", "MEAR", "MEAS", "MEON", "MIAR",
    "MION", "MOCO", "MOKO", "MULA", "MULO", "NACA", "NACO", "PEDA",
    "PEDO", "PENE", "PIPI", "PITO", "POPO", "PUTA", "PUTO", "QULO",
    "RATA", "ROBA", "ROBE", "ROBO", "RUIN", "SENO", "TETA", "VACA",
    "VAGA", "VAGO", "VAKA", "VUEI", "VUEY", "WUEI", "WUEY",
}


def censurar_si_inconveniente(cuatro_letras: str) -> str:
    """Sustituye la última letra por 'X' si las 4 letras son inconvenientes."""
    if cuatro_letras.upper() in PALABRAS_INCONVENIENTES:
        return cuatro_letras[:3] + "X"
    return cuatro_letras
