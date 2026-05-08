"""Handler del complemento IEDU (instituciones educativas / colegiaturas).

Enmascara nombre y CURP del alumno, el autRVOE y el RFC de quien paga. El
nombre de la escuela es el Emisor del CFDI y lo enmascara el handler base.
"""

from .base import NS_IEDU, Handler, MaskContext, buscar, namespace_presente, registrar


@registrar
class HandlerIEDU(Handler):
    nombre = "iedu"

    def aplica(self, root) -> bool:
        return namespace_presente(root, NS_IEDU)

    def enmascarar(self, root, ctx: MaskContext) -> None:
        for inst in buscar(root, "instEducativas", NS_IEDU):
            real_nombre = inst.get("nombreAlumno")
            real_curp = inst.get("CURP")
            if real_nombre or real_curp:
                # El que paga la colegiatura (Receptor) es el padre/madre; el
                # alumno hereda su apellido según el género.
                fake_nombre, fake_curp = ctx.factory.alumno(
                    real_nombre, real_curp, padre=ctx.receptor_entidad)
                if real_nombre:
                    inst.set("nombreAlumno", fake_nombre)
                    ctx._conteo("iedu.nombreAlumno")
                if real_curp and fake_curp:
                    inst.set("CURP", fake_curp)
                    ctx._conteo("iedu.curp")
            ctx.remap_attr(inst, "autRVOE", ctx.factory.aut_rvoe, "iedu.autRVOE")
            ctx.remap_attr(inst, "rfcPago", ctx.rfc, "iedu.rfcPago")
