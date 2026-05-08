"""Fábrica de datos falsos CONSISTENTES.

Regla de consistencia: la misma entidad real (por RFC) mapea SIEMPRE al mismo
fake en todos los archivos. Unicidad: dos entidades reales distintas nunca
colisionan en un mismo fake. Todo lo generado se persiste en `MappingDB` para
poder revertir.

`seed` hace la generación reproducible; la base de mapeo es la fuente de verdad
para revertir.
"""

from __future__ import annotations

import base64
import random
import uuid as _uuid
from datetime import date, timedelta

from rfcgen import curp as gen_curp
from rfcgen import rfc_fisica, rfc_moral

from .mapping_db import EntidadFalsa, MappingDB
from .nombres_db import NombresDB

# RFC genéricos que NO se enmascaran (no son PII).
RFC_PASSTHROUGH = {"XAXX010101000", "XEXX010101000"}

_EPOCH = date(1970, 1, 1)
_DEPARTAMENTOS = ["Ventas", "Administración", "Operaciones", "Sistemas",
                  "Recursos Humanos", "Logística", "Contabilidad", "Almacén"]
_PUESTOS = ["Auxiliar", "Analista", "Coordinador", "Gerente", "Supervisor",
            "Operador", "Asistente", "Encargado"]


class FakeFactory:
    def __init__(self, nombres: NombresDB, mapping: MappingDB,
                 seed: int | None = None):
        self.nombres = nombres
        self.mapping = mapping
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Entidades (Emisor / Receptor)
    # ------------------------------------------------------------------
    @staticmethod
    def tipo_por_rfc(rfc: str) -> str:
        return "fisica" if len(rfc.strip()) == 13 else "moral"

    def entidad(self, real_rfc: str, real_name: str = "",
                real_curp: str | None = None) -> EntidadFalsa:
        real_rfc = (real_rfc or "").strip().upper()

        if real_rfc in RFC_PASSTHROUGH:
            # Genérico: se conserva tal cual (no es dato identificable).
            return EntidadFalsa(real_rfc, real_name, real_curp,
                                self.tipo_por_rfc(real_rfc), real_rfc,
                                real_name, real_curp, "")

        existente = self.mapping.buscar_entidad_por_real(real_rfc)
        if existente:
            return existente

        tipo = self.tipo_por_rfc(real_rfc)
        ent = self._generar_entidad(real_rfc, real_name, real_curp, tipo)
        self.mapping.insertar_entidad(ent)
        return ent

    def _generar_entidad(self, real_rfc, real_name, real_curp, tipo) -> EntidadFalsa:
        for _ in range(50):  # reintentos por unicidad del fake_rfc
            if tipo == "fisica":
                fecha = self._fecha_aleatoria(1955, 2004)
                genero = self.rng.choice("HM")
                nombre = self.nombres.nombre_pila(genero, self.rng)
                paterno, materno = self.nombres.dos_apellidos(self.rng)
                fake_name = f"{nombre} {paterno} {materno}"
                fake_rfc = rfc_fisica(nombre, paterno, materno, fecha, self.rng)
                fake_curp = gen_curp(nombre, paterno, materno, fecha, genero,
                                     rng=self.rng)
            else:
                fecha = self._fecha_aleatoria(1980, 2021)
                genero = paterno = materno = None
                fake_name = self.nombres.razon_social(self.rng)
                fake_rfc = rfc_moral(fake_name, fecha, self.rng)
                fake_curp = None

            if not self.mapping.fake_rfc_existe(fake_rfc):
                return EntidadFalsa(
                    real_rfc=real_rfc, real_name=real_name,
                    real_curp=real_curp, tipo=tipo, fake_rfc=fake_rfc,
                    fake_name=fake_name, fake_curp=fake_curp,
                    fecha_iso=fecha.isoformat(),
                    genero=genero, ap_paterno=paterno, ap_materno=materno,
                )
        raise RuntimeError("No se pudo generar un RFC falso único")

    def _fecha_aleatoria(self, anio_min: int, anio_max: int) -> date:
        ini = date(anio_min, 1, 1)
        fin = date(anio_max, 12, 28)
        dias = (fin - ini).days
        return ini + timedelta(days=self.rng.randint(0, dias))

    # ------------------------------------------------------------------
    # Valores genéricos (CP, NSS, sellos, UUID, cuentas, ...)
    # ------------------------------------------------------------------
    def _valor_unico(self, kind: str, real_value: str, generador) -> str:
        """Devuelve (y persiste) un fake consistente para (kind, real_value)."""
        if real_value is None:
            return real_value
        existente = self.mapping.buscar_valor(kind, real_value)
        if existente is not None:
            return existente
        for _ in range(100):
            fake = generador()
            if fake != real_value and not self.mapping.fake_valor_existe(kind, fake):
                self.mapping.insertar_valor(kind, real_value, fake)
                return fake
        raise RuntimeError(f"No se pudo generar valor único para {kind}")

    def registrar_valor_fijo(self, kind: str, real_value: str, fake_value: str) -> str:
        """Persiste un mapeo real->fake YA decidido (p. ej. CURP atado a una
        entidad) para que sea reversible. Idempotente por (kind, real_value)."""
        if real_value is None:
            return fake_value
        existente = self.mapping.buscar_valor(kind, real_value)
        if existente is not None:
            return existente
        if not self.mapping.fake_valor_existe(kind, fake_value):
            self.mapping.insertar_valor(kind, real_value, fake_value)
        return fake_value

    def curp_valor(self, real: str) -> str:
        """CURP falsa independiente y reversible (sin entidad asociada)."""
        def gen():
            g = self.rng.choice("HM")
            n = self.nombres.nombre_pila(g, self.rng)
            p, m = self.nombres.dos_apellidos(self.rng)
            f = self._fecha_aleatoria(1960, 2004)
            return gen_curp(n, p, m, f, g, rng=self.rng)
        return self._valor_unico("curp", real, gen)

    def cp(self, real_cp: str) -> str:
        return self._valor_unico("cp", real_cp,
                                 lambda: f"{self.rng.randint(1000, 99999):05d}")

    def uuid(self, real: str) -> str:
        return self._valor_unico("uuid", real,
                                 lambda: str(_uuid.UUID(int=self.rng.getrandbits(128))).upper())

    def no_certificado(self, real: str) -> str:
        return self._valor_unico("no_certificado", real, lambda: self._digitos(20))

    def sello(self, real: str) -> str:
        # El sello no debe mantenerse (rompe XSD igual, y puede filtrar datos).
        return self._valor_unico("sello", real,
                                 lambda: self._base64_aleatorio(len(real) or 344))

    def certificado(self, real: str) -> str:
        # ⚠️ El certificado base64 embebe el RFC y nombre legal REALES.
        return self._valor_unico("certificado", real,
                                 lambda: self._base64_aleatorio(len(real) or 1400))

    def nss(self, real: str) -> str:
        return self._valor_unico("nss", real, lambda: self._digitos(11))

    def registro_patronal(self, real: str) -> str:
        return self._valor_unico(
            "registro_patronal", real,
            lambda: self.rng.choice("ABCDEFGHIJKLMNPQRSTUVWXYZ") + self._digitos(10))

    def cuenta(self, real: str) -> str:
        # Conserva la longitud del original.
        return self._valor_unico("cuenta", real,
                                 lambda: self._digitos(len(real) or 11))

    def num_empleado(self, real: str) -> str:
        return self._valor_unico("num_empleado", real,
                                 lambda: self._digitos(len(real) or 4))

    def departamento(self, real: str) -> str:
        return self._valor_unico("departamento", real,
                                 lambda: self.rng.choice(_DEPARTAMENTOS))

    def puesto(self, real: str) -> str:
        return self._valor_unico("puesto", real,
                                 lambda: self.rng.choice(_PUESTOS))

    def fecha_laboral(self, real: str) -> str:
        # Mantiene formato YYYY-MM-DD, jitter de algunos días.
        return self._valor_unico("fecha_laboral", real,
                                 lambda: self._jitter_fecha(real))

    def salario_jitter(self, real: str) -> str:
        """Altera un salario +/-7% (reproducible y reversible)."""
        def gen():
            try:
                val = float(real)
            except (TypeError, ValueError):
                return real
            return f"{val * self.rng.uniform(0.93, 1.07):.2f}"
        return self._valor_unico("salario", real, gen)

    def aut_rvoe(self, real: str) -> str:
        return self._valor_unico("aut_rvoe", real,
                                 lambda: self._digitos(len(real) or 8))

    def escuela(self, real: str) -> str:
        return self._valor_unico("escuela", real,
                                 lambda: self.nombres.escuela(self.rng))

    def alumno(self, real_nombre: str | None, real_curp: str | None,
               padre: "EntidadFalsa | None" = None) -> tuple[str | None, str | None]:
        """Nombre (y CURP) de alumno falsos, consistentes entre sí y reversibles.

        Si se da `padre` (el Emisor/Receptor que paga, persona física), el
        alumno COMPARTE apellido con él según su género:
          - padre HOMBRE  -> comparten apellido PATERNO
          - madre MUJER   -> comparten apellido MATERNO
        El otro apellido se genera al azar.

        Cada valor real se guarda bajo SU propia clave (no se mezclan), para
        que el modo revertir restaure el nombre y la CURP correctos.
        """
        nombre_fake = (self.mapping.buscar_valor("alumno_nombre", real_nombre)
                       if real_nombre else None)
        curp_fake = (self.mapping.buscar_valor("alumno_curp", real_curp)
                     if real_curp else None)

        falta_nombre = real_nombre and nombre_fake is None
        falta_curp = real_curp and curp_fake is None
        if falta_nombre or falta_curp:
            # Generar UNA persona coherente (nombre + CURP del mismo individuo).
            genero = self.rng.choice("HM")
            n = self.nombres.nombre_pila(genero, self.rng)
            pat, mat = self._apellidos_alumno(padre)
            fecha = self._fecha_aleatoria(2000, 2018)
            if falta_nombre:
                nombre_fake = self.registrar_valor_fijo(
                    "alumno_nombre", real_nombre, f"{n} {pat} {mat}")
            if falta_curp:
                curp_fake = self.registrar_valor_fijo(
                    "alumno_curp", real_curp,
                    gen_curp(n, pat, mat, fecha, genero, rng=self.rng))
        return nombre_fake, curp_fake

    def _apellidos_alumno(self, padre) -> tuple[str, str]:
        """Apellidos del alumno; hereda del padre/madre según su género."""
        pat, mat = self.nombres.dos_apellidos(self.rng)
        if padre is not None and padre.tipo == "fisica" and padre.genero:
            if padre.genero == "H" and padre.ap_paterno:
                pat = padre.ap_paterno            # hereda apellido paterno
            elif padre.genero == "M" and padre.ap_materno:
                mat = padre.ap_materno            # hereda apellido materno
        return pat, mat

    # ------------------------------------------------------------------
    # Generadores de bajo nivel
    # ------------------------------------------------------------------
    def _digitos(self, n: int) -> str:
        return "".join(str(self.rng.randint(0, 9)) for _ in range(n))

    def _base64_aleatorio(self, n_chars: int) -> str:
        n_bytes = max(8, (n_chars * 3) // 4)
        crudo = bytes(self.rng.getrandbits(8) for _ in range(n_bytes))
        return base64.b64encode(crudo).decode("ascii")

    def _jitter_fecha(self, real: str) -> str:
        try:
            y, m, d = (int(x) for x in real[:10].split("-"))
            base = date(y, m, d)
        except Exception:
            base = self._fecha_aleatoria(2005, 2022)
        nueva = base + timedelta(days=self.rng.randint(-20, 20))
        return nueva.isoformat()
