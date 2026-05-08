"""Handler del complemento de Nómina 1.2.

Enmascara datos del trabajador y del patrón. Por defecto CONSERVA los salarios
(SDI/SBC); si `ctx.jitter_salarios` está activo, los altera ligeramente.
"""

from .base import (NS_NOMINA12, Handler, MaskContext, buscar,
                   namespace_presente, registrar)

_SALARIOS = ("SalarioDiarioIntegrado", "SalarioBaseCotApor")


@registrar
class HandlerNomina(Handler):
    nombre = "nomina12"

    def aplica(self, root) -> bool:
        return namespace_presente(root, NS_NOMINA12)

    def enmascarar(self, root, ctx: MaskContext) -> None:
        # Emisor de nómina (patrón). Si el patrón es persona física trae Curp.
        for emisor in buscar(root, "Emisor", NS_NOMINA12):
            ctx.remap_attr(emisor, "RegistroPatronal",
                           ctx.factory.registro_patronal, "nomina.registroPatronal")
            ctx.remap_attr(emisor, "RfcPatronOrigen", ctx.rfc,
                           "nomina.rfcPatronOrigen")
            self._curp_atado(emisor, ctx, ctx.emisor_entidad, "nomina.curpEmisor")

        # Receptor de nómina (trabajador)
        for receptor in buscar(root, "Receptor", NS_NOMINA12):
            self._curp_atado(receptor, ctx, ctx.receptor_entidad, "nomina.curp")
            ctx.remap_attr(receptor, "NumSeguridadSocial", ctx.factory.nss,
                           "nomina.nss")
            ctx.remap_attr(receptor, "NumEmpleado", ctx.factory.num_empleado,
                           "nomina.numEmpleado")
            ctx.remap_attr(receptor, "Departamento", ctx.factory.departamento,
                           "nomina.departamento")
            ctx.remap_attr(receptor, "Puesto", ctx.factory.puesto, "nomina.puesto")
            ctx.remap_attr(receptor, "CuentaBancaria", ctx.factory.cuenta,
                           "nomina.cuentaBancaria")
            ctx.remap_attr(receptor, "FechaInicioRelLaboral",
                           ctx.factory.fecha_laboral, "nomina.fechaInicioRel")

            if ctx.jitter_salarios:
                for attr in _SALARIOS:
                    ctx.remap_attr(receptor, attr, ctx.factory.salario_jitter,
                                   f"nomina.{attr}")

    def _curp_atado(self, el, ctx: MaskContext, entidad, etiqueta: str) -> None:
        """Enmascara @Curp atándola al fake_curp de la entidad dada (para que
        RFC y CURP de la misma persona sean coherentes)."""
        real_curp = el.get("Curp")
        if not real_curp:
            return
        if entidad is not None and entidad.fake_curp:
            fake = ctx.factory.registrar_valor_fijo("curp", real_curp, entidad.fake_curp)
        else:
            fake = ctx.factory.curp_valor(real_curp)
        el.set("Curp", fake)
        ctx._conteo(etiqueta)
