# Doc-formatter Negocios

> **Compilador Editorial Determinista de Propuestas Técnicas y Documentos Corporativos**
> Diseñado según la arquitectura estricta `engine-vs-profile`, garantizando cero sesgos (0%), determinismo absoluto (100%) y estética editorial de publicación científica.

---

## 1. Visión General

**Doc-formatter Negocios** es una distribución especializada y perfilada de *Doc-formatter* optimizada para la generación determinista de documentos corporativos, informes de pre-factibilidad, propuestas técnicas de ingeniería y reportes ejecutivos de consultoría.

A partir de fuentes en formato **DocSource** (Markdown estructurado con contratos de metadatos en YAML), el sistema genera documentos Word OpenXML (`.docx`) y versiones de alta fidelidad en PDF con calidad tipográfica equivalente a revistas científicas y editoriales de primer nivel.

### Principales Capacidades
- **Tipografía Formal Hermann Zapf**: Basado en *Palatino Linotype*, interlineado armónico 1.15 y jerarquía de tamaños calibrada contra el estándar *The Elements of Typographic Style*.
- **Reglas Horizontales Subtitulares**: Líneas divisorias deterministas de 0.5 pt en color Process Cyan (`#0097B2`) para encabezados de sección.
- **Tablas LaTeX Booktabs**: Cero rejillas de Word por defecto; tablas con regla superior e inferior gruesas (0.75 pt), regla divisoria de cabecera (0.5 pt), padding balanceado y propiedades nativas `w:cantSplit` y `w:tblHeader` para evitar roturas de página.
- **Distribución Ejecutiva Calibrada**: Maquetación sin páginas huérfanas ni desbordes, logrando exactamente 13 páginas (1 portada minimalista + 12 capítulos auto-contenidos de una página).
- **Quality Gate PyMuPDF Integrado**: Verificación determinista de 0 páginas en blanco y densidad estructural.

---

## 2. Arquitectura: `engine-vs-profile`

El proyecto implementa una estricta separación de responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                       DocSource AST                         │
│         (Markdown Canónico + Metadatos document.yaml)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 MOTOR DETERMINISTA (src/)                   │
│  - Agnóstico a instituciones, clientes y dominios           │
│  - Compilador de AST a OpenXML (DOCX)                       │
│  - Evaluación de plantillas secuenciales ("{n}   {title}")  │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│    PERFILES (profiles/)      │    │     PIPELINE (scripts/)      │
│  - sig-pmo/inception@1.yaml  │    │  - build_corporate_proposal  │
│  - sig-pmo/proposal@1.yaml   │    │  - Pure OpenXML assembly     │
│  - Reglas tipográficas       │    │  - PyMuPDF Quality Gate      │
└──────────────────────────────┘    └──────────────────────────────┘
```

1. **El Motor (`src/doc_formatter/`)**:
   - Nunca contiene cadenas o reglas atadas a una empresa, cliente o universidad.
   - Implementa contadores secuenciales estrictos para títulos (`chapter_n`).
2. **Los Perfiles (`profiles/sig-pmo/`)**:
   - Definen declarativamente fuentes, márgenes A4 (2.5 cm), colores de acento, esquemas de capítulos requeridos y reglas de numeración.
3. **El Pipeline (`scripts/build_corporate_proposal.py`)**:
   - Ensambla la portada y el cuerpo en OpenXML puro sin intermediación destructiva de aplicaciones externas.
   - Todos los campos se leen dinámicamente de `document.yaml`, con fallbacks neutros.

---

## 3. Certificación de Auditoría: Cero Sesgos (0%)

El código fue sometido a auditoría estricta de determinismo y ausencia de sesgos contra especificaciones de arquitectura y validación determinista.

| Dimensión Auditada | Resultado | Evidencia Técnica |
| :--- | :---: | :--- |
| **Determinismo en Salida** | **100%** | Sin uso de marcas de tiempo no sembradas, números aleatorios ni ordenamiento dependiente del SO. Mismas entradas producen bit a bit el mismo documento. |
| **Ausencia de Sesgos en Motor** | **100%** | `src/doc_formatter/layout.py` libre de cadenas de dominio o cliente. |
| **Parametrización de Datos** | **100%** | Metadatos desacoplados en `docsource/document.yaml`. |
| **Ensamble Nativo OpenXML** | **100%** | Portada y secciones unificadas directamente en OpenXML mediante `python-docx` y `oxml`. |
| **Quality Gate** | **PASS** | 13 páginas ejecutivas exactas, 0 páginas en blanco verificadas por PyMuPDF. |

*Para ver el informe detallado de auditoría, consultar [AUDITORIA_DETERMINISMO_SESGOS.md](AUDITORIA_DETERMINISMO_SESGOS.md).*

---

## 4. Estructura del Repositorio

```
doc-formatter-negocios/
├── src/
│   └── doc_formatter/          # Motor agnóstico de compilación
├── profiles/
│   └── sig-pmo/
│       ├── inception@1.yaml    # Perfil corporativo de pre-factibilidad
│       └── proposal@1.yaml     # Perfil de propuesta técnica completa
├── docsource/                  # Entrada canónica DocSource de prueba
│   ├── document.yaml           # Metadatos del documento
│   ├── 01-ficha-tecnica.md
│   ├── 02-resumen-ejecutivo.md
│   ├── ...
│   └── 12-aceptacion-firmas.md
├── scripts/
│   └── build_corporate_proposal.py  # Pipeline editorial determinista V3.1
├── AUDITORIA_DETERMINISMO_SESGOS.md # Certificación de calidad y sesgos
├── pyproject.toml              # Definición del paquete
└── README.md                   # Documentación principal
```

---

## 5. Instalación y Uso

### Requisitos Previos
- Python 3.10 o superior
- Pandoc 3.x (en el PATH del sistema)
- Word (Windows) o LibreOffice (`soffice` en Linux/macOS) para la exportación final a PDF

### Instalación
```bash
git clone https://github.com/chihuacoaudaz-png/doc-formatter-negocios.git
cd doc-formatter-negocios
pip install -e .
pip install -r requirements-dev.txt
pip install pymupdf pyyaml
```

### Ejecución del Pipeline Editorial
Para compilar la propuesta de ejemplo, aplicar la cirugía tipográfica y verificar la salida:

```bash
python scripts/build_corporate_proposal.py
```

Los artefactos generados se guardarán en la carpeta `dist/`:
- `dist/PROPUESTA_TECNICA_SIG_PMO_FORMATEADO.docx`: Documento Word final estilizado.
- `dist/FORMATO_MAESTRO_SIG_PMO_PLANTILLA.docx`: Plantilla base reutilizable.
- `dist/PROPUESTA_TECNICA_SIG_PMO_FORMATEADO.pdf`: Documento PDF de alta definición de 13 páginas.
- `dist/renders/`: Vistas previas en imagen (`page_1.png` a `page_13.png`) generadas por el auditor.

---

## 6. Licencia y Atribución

Este repositorio es mantenido de forma independiente como perfil de negocios para *Doc-formatter*.
Licencia: MIT.
