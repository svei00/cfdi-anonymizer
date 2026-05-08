"""Construcción de rutas de la Bóveda."""

from __future__ import annotations

from pathlib import Path

EMITIDAS = "Emitidas"
RECIBIDAS = "Recibidas"
# "Bóveda" se usa por defecto; puede cambiarse para no confundir con MiAdminXML.
CARPETA_BOVEDA_DEFAULT = "Bóveda"


def clasificacion(target_rfc: str, emisor_rfc: str, receptor_rfc: str) -> str | None:
    """'Emitidas' si el RFC objetivo emitió, 'Recibidas' si recibió, None si
    no participa."""
    t = (target_rfc or "").strip().upper()
    if t and t == (emisor_rfc or "").strip().upper():
        return EMITIDAS
    if t and t == (receptor_rfc or "").strip().upper():
        return RECIBIDAS
    return None


def anio_mes_de_fecha(fecha_iso: str) -> tuple[str, str]:
    """De 'YYYY-MM-DD...' o 'YYYY-MM-DDThh:mm:ss' devuelve ('YYYY', 'MM')."""
    fecha_iso = (fecha_iso or "").strip()
    anio = fecha_iso[0:4] or "0000"
    mes = fecha_iso[5:7] if len(fecha_iso) >= 7 else "00"
    return anio, mes


def ruta_relativa(rfc: str, clasif: str, fecha_iso: str) -> Path:
    """Ruta relativa <RFC>/<Emitidas|Recibidas>/<YYYY>/<MM>."""
    anio, mes = anio_mes_de_fecha(fecha_iso)
    return Path(rfc.strip().upper()) / clasif / anio / mes


def ruta_boveda(raiz: Path | str, app_name: str, rfc: str, clasif: str,
                fecha_iso: str, *, carpeta_boveda: str = CARPETA_BOVEDA_DEFAULT,
                crear: bool = False) -> Path:
    """Ruta absoluta completa de la carpeta destino dentro de la Bóveda."""
    ruta = (Path(raiz) / app_name / carpeta_boveda
            / ruta_relativa(rfc, clasif, fecha_iso))
    if crear:
        ruta.mkdir(parents=True, exist_ok=True)
    return ruta
