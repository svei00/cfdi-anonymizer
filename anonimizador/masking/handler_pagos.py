"""Handler del complemento de Pagos (2.0 y 1.0 legado).

Enmascara cuentas y RFC de bancos ordenante/beneficiario, y los UUID de los
documentos relacionados (IdDocumento) para que sigan siendo consistentes.
"""

from .base import (NS_PAGOS10, NS_PAGOS20, Handler, MaskContext, buscar,
                   namespace_presente, registrar)


@registrar
class HandlerPagos(Handler):
    nombre = "pagos"

    def aplica(self, root) -> bool:
        return (namespace_presente(root, NS_PAGOS20)
                or namespace_presente(root, NS_PAGOS10))

    def enmascarar(self, root, ctx: MaskContext) -> None:
        for ns in (NS_PAGOS20, NS_PAGOS10):
            for pago in buscar(root, "Pago", ns):
                ctx.remap_attr(pago, "RfcEmisorCtaOrd", ctx.rfc, "pagos.rfcCtaOrd")
                ctx.remap_attr(pago, "RfcEmisorCtaBen", ctx.rfc, "pagos.rfcCtaBen")
                ctx.remap_attr(pago, "CtaOrdenante", ctx.factory.cuenta,
                               "pagos.ctaOrdenante")
                ctx.remap_attr(pago, "CtaBeneficiario", ctx.factory.cuenta,
                               "pagos.ctaBeneficiario")
            for docto in buscar(root, "DoctoRelacionado", ns):
                ctx.remap_attr(docto, "IdDocumento", ctx.factory.uuid,
                               "pagos.idDocumento")
