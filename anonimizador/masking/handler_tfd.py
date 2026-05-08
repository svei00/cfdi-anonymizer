"""Handler del Timbre Fiscal Digital (TFD 1.0 / 1.1)."""

from .base import (NS_TFD, Handler, MaskContext, buscar, namespace_presente,
                   registrar)


@registrar
class HandlerTFD(Handler):
    nombre = "tfd"

    def aplica(self, root) -> bool:
        return namespace_presente(root, NS_TFD)

    def enmascarar(self, root, ctx: MaskContext) -> None:
        for tfd in buscar(root, "TimbreFiscalDigital", NS_TFD):
            ctx.remap_attr(tfd, "UUID", ctx.factory.uuid, "tfd.uuid")
            ctx.remap_attr(tfd, "SelloCFD", ctx.factory.sello, "tfd.selloCFD")
            ctx.remap_attr(tfd, "SelloSAT", ctx.factory.sello, "tfd.selloSAT")
            ctx.remap_attr(tfd, "NoCertificadoSAT", ctx.factory.no_certificado,
                           "tfd.noCertificadoSAT")
