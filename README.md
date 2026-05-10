# CFDI Anonymizer ("XML Renamer")

Convierte CFDI XML mexicanos REALES en copias MOCK anonimizadas, para usarlas
como datos de demo/prueba seguros. Reemplaza datos identificables por datos
falsos **consistentes**, conserva importes/impuestos/conceptos/fechas, y es
**reversible** gracias a un mapeo persistido en SQLite.

> Los archivos enmascarados **no** son válidos para el SAT (el Sello no
> coincide), pero **sí parsean** como XML. Son para demos/pruebas, no para
> timbrar.

## Requisitos

- Python 3.11+ (probado en 3.14)
- `pip install -r requirements.txt`  (sólo `lxml`)

## Uso (GUI)

- **Windows**: doble clic en **`Ejecutar.bat`** (instala dependencias la 1ª vez).
- **Linux/macOS**: `chmod +x ejecutar.sh` y luego `./ejecutar.sh`.
- **Manual** (cualquier SO):

```
python main.py
```

1. **Carpeta de origen**: donde están los XML reales (se busca recursivamente).
2. **Carpeta de destino**: donde se escriben los mocks.
3. **Carpeta de mapeo/semilla**: dónde vive `mapeo.sqlite` (por defecto = destino).
4. Opciones: conservar originales, estructura Bóveda, alterar salarios de
   Nómina, **modo revertir**, semilla.
5. **Ejecutar**.

### Modo Bóveda (espejo)

Si tu origen ya es una Bóveda existente con la estructura
`<RFC>/<Emitidas|Recibidas>/<yyyy>/<MM>/` (p. ej. `C:\AdminXML\BovedaCFDI`),
marca **"El origen es una Bóveda"**. La app:

- **Refleja** el árbol en el destino, **renombrando sólo la carpeta de RFC** a
  su RFC falso (consistente); conserva `Emitidas/Recibidas/yyyy/MM` y NO crea
  carpetas nuevas.
- Enmascara **todas las partes** de cada XML (titular y contrapartes), de forma
  consistente entre clientes.
- **Valida** que cada archivo de `Emitidas/` tenga `cfdi:Emisor` = RFC de la
  carpeta (y `Recibidas/` → `cfdi:Receptor`). Si algo está desubicado, lo
  enmascara igual y lo reporta como AVISO. Las carpetas que no son RFC se
  ignoran con aviso.

Para **revertir**: marca "Modo revertir" (con o sin "El origen es una Bóveda",
según corresponda), pon como origen la carpeta de mocks y apunta la carpeta de
mapeo al `mapeo.sqlite` usado al enmascarar.

## Qué se enmascara / qué se conserva

- **Se enmascara** (consistente): RFC y Nombre de Emisor/Receptor; CP
  (LugarExpedicion, DomicilioFiscalReceptor); Sello, NoCertificado y
  Certificado (⚠️ el Certificado embebe el RFC y nombre reales); TFD (UUID,
  SelloCFD, SelloSAT, NoCertificadoSAT); Nómina (CURP, NSS, RegistroPatronal,
  cuenta, NumEmpleado, Departamento, Puesto, FechaInicioRelLaboral); Pagos
  (cuentas y RFC de bancos, IdDocumento); IEDU (nombreAlumno, CURP, autRVOE,
  rfcPago).
- **Se conserva**: importes (SubTotal, Total, impuestos), Conceptos/Descripción,
  fechas de la transacción, TipoDeComprobante, Versión y namespaces.
- **Salarios** (SDI/SBC): se conservan por defecto; toggle para alterarlos.

## Arquitectura

```
rfcgen/        Módulo REUTILIZABLE: generación de RFC y CURP (sin dependencias).
boveda/        Módulo REUTILIZABLE: estructura de carpetas Bóveda.
anonimizador/  Lógica de la app:
  seed_nombres.py   Datos semilla (nombres/empresas/escuelas).
  nombres_db.py     Catálogo SQLite de nombres falsos.
  mapping_db.py     Mapeo real<->fake (entity_map, value_map, file_map).
  fake_factory.py   Generación de fakes CONSISTENTES + unicidad.
  masking/          Motor por handlers (escalable):
    base.py           Registro, contexto y utilidades.
    handler_cfdi.py   Comprobante/Emisor/Receptor (3.3, 4.0 y futuras).
    handler_tfd.py    Timbre Fiscal Digital.
    handler_nomina.py Nómina 1.2.
    handler_pagos.py  Pagos 2.0 / 1.0.
    handler_iedu.py   IEDU / Colegiaturas.
    engine.py         Orquestación de un archivo.
  revertir.py       Modo revertir (genérico).
  procesador.py     Orquestador de carpetas + Bóveda.
  gui.py            Interfaz Tkinter.
main.py          Punto de entrada.
muestras_sinteticas/  Fixtures CFDI 4.0 sintéticos para pruebas.
```

### Agregar un complemento nuevo

Crea un `handler_*.py` con una clase que herede de `Handler`, decorada con
`@registrar`, e impórtala en `anonimizador/masking/__init__.py`. No hay listas
planas que tocar: el handler se autoregistra.

## Demos / pruebas rápidas

```
python -m rfcgen          # demo del generador de RFC/CURP
```
