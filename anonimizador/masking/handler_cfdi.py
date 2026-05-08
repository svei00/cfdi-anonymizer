"""Handler base del CFDI (todas las versiones: 3.3, 4.0, futuras).

Enmascara los datos identificables a nivel Comprobante / Emisor / Receptor.
Mantiene SIN CAMBIO importes, impuestos, conceptos, fechas, versión y
namespaces.
"""

from .base import (Handler, MaskContext, cfdi_namespace, hijos_directos,
                   registrar)


@registrar
class HandlerCFDI(Handler):
    nombre = "cfdi"

    def aplica(self, root) -> bool:
        return cfdi_namespace(root) is not None

    def enmascarar(self, root, ctx: MaskContext) -> None:
        # --- Comprobante (raíz) ---------------------------------------
        # Sello y Certificado: ⚠️ el Certificado base64 embebe RFC+nombre real.
        ctx.remap_attr(root, "Sello", ctx.factory.sello, "comprobante.sello")
        ctx.remap_attr(root, "Certificado", ctx.factory.certificado,
                       "comprobante.certificado")
        ctx.remap_attr(root, "NoCertificado", ctx.factory.no_certificado,
                       "comprobante.noCertificado")
        ctx.remap_attr(root, "LugarExpedicion", ctx.factory.cp,
                       "comprobante.lugarExpedicion")

        # --- Emisor ----------------------------------------------------
        for emisor in hijos_directos(root, "Emisor"):
            rfc = emisor.get("Rfc")
            if rfc:
                ent = ctx.factory.entidad(rfc, emisor.get("Nombre", ""))
                emisor.set("Rfc", ent.fake_rfc)
                if emisor.get("Nombre"):
                    emisor.set("Nombre", ent.fake_name)
                ctx.emisor_entidad = ent
                ctx._conteo("emisor")

        # --- Receptor --------------------------------------------------
        for receptor in hijos_directos(root, "Receptor"):
            rfc = receptor.get("Rfc")
            if rfc:
                ent = ctx.factory.entidad(rfc, receptor.get("Nombre", ""))
                receptor.set("Rfc", ent.fake_rfc)
                if receptor.get("Nombre"):
                    receptor.set("Nombre", ent.fake_name)
                ctx.receptor_entidad = ent
                ctx._conteo("receptor")
            # CP del domicilio fiscal del receptor (CFDI 4.0).
            ctx.remap_attr(receptor, "DomicilioFiscalReceptor", ctx.factory.cp,
                           "receptor.domicilioFiscal")
