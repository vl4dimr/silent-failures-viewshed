# -*- coding: utf-8 -*-
"""
Paquete de envio a Journal of Archaeological Method and Theory (Springer).

Springer pide el manuscrito en Word con la portada dentro (revision de anonimo
simple), las figuras nombradas «Fig1», «Fig2», … y una carta de presentacion.
Este guion copia el manuscrito ya generado y auditado, renombra las figuras
como exige la norma y redacta la carta con cifras leidas del propio manuscrito,
para que no se desvien de el.

Salida: ENVIO_JAMT/
    1_MANUSCRIPT.docx
    2_COVER_LETTER.docx  (+ .txt para pegar en Editorial Manager)
    Fig1.png … Fig4.png  (+ Fig1.svg, el pipeline en vectorial)
"""
import os
import re
import shutil
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docmeta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "results", "figuras")
MS = os.path.join(BASE, "manuscript_silent_failures.docx")
OUT = os.path.join(BASE, "ENVIO_JAMT")
os.makedirs(OUT, exist_ok=True)

AUTOR = "Milton Vladimir Mamani Calisaya"
FILIACION = "Universidad Nacional del Altiplano, Puno, Peru"
CORREO = "mmamanic@unap.edu.pe"
ORCID = "0000-0002-0676-0989"
DOI_ESTE = "10.5281/zenodo.22242923"

# ----------------------------------------------------------- cifras del manuscrito
src = Document(MS)
ps = [p.text.strip() for p in src.paragraphs]
titulo = ps[0] + ": " + ps[1][0].lower() + ps[1][1:]
i_ab, i_kw = ps.index("Abstract"), ps.index("Keywords")
n_abs = len(" ".join(ps[i_ab + 1:i_kw]).split())
i_ini = next(i for i, t in enumerate(ps) if t.startswith("1. Introduction"))
i_dec = ps.index("Statements and Declarations")
i_ref = ps.index("References")
n_cuerpo = sum(len(t.split()) for t in ps[i_ini:i_dec])
n_cuerpo += sum(len(c.text.split()) for t in src.tables for r in t.rows for c in r.cells)
n_refs = len([t for t in ps[i_ref + 1:] if re.match(r"^[^\W\d_][\w' -]*?, [A-Z]\.", t)])
n_fig = len(src.inline_shapes)
n_tab = len(src.tables)

# ------------------------------------------------------------------- copias
shutil.copyfile(MS, os.path.join(OUT, "1_MANUSCRIPT.docx"))
for n, fn in enumerate(["fig_pipeline.png", "fig_anatomia.png", "fig_laboratorio.png",
                        "fig_consecuencias.png"], start=1):
    shutil.copyfile(os.path.join(FIG, fn), os.path.join(OUT, "Fig%d.png" % n))
shutil.copyfile(os.path.join(FIG, "fig_pipeline.svg"), os.path.join(OUT, "Fig1.svg"))

# ------------------------------------------------------------------- carta
CARTA = [
    "Dear Editors,",

    "Please consider the enclosed manuscript, “%s”, for publication in the Journal of "
    "Archaeological Method and Theory as a research article. It is original, is not under "
    "consideration elsewhere, and all data and code are openly deposited with a persistent "
    "identifier (https://doi.org/%s)." % (titulo, DOI_ESTE),

    "The paper addresses a gap between two things the discipline now rightly demands, and that "
    "this journal has done much to establish: computational reproducibility and computational "
    "correctness. A reproducible pipeline reproduces its errors faithfully. The manuscript "
    "characterises a class of defects in visibility analysis that crash nothing, produce plausible "
    "output, survive both peer review and re-execution, and invert or erase the conclusion of the "
    "study containing them; three were recently documented, and corrected, in an intervisibility "
    "study in the Titicaca basin whose pre-correction runs are deposited alongside the corrected "
    "ones.",

    "Three methodological contributions follow. An executable benchmark for line-of-sight engines "
    "whose expectations are derived rather than written by hand and whose adequacy is measured by "
    "mutation analysis; a synthetic-landscape laboratory in which the truth is known by "
    "construction, so that what each design defect does to statistical inference is measured "
    "against an exact expectation; and a measurement of two engines in everyday archaeological "
    "use, GDAL and GRASS through QGIS, which pass every benchmark case when configured deliberately "
    "and contradict each other on nearly half of them at their shipped defaults. The defect, in "
    "other words, need not be in the code: it can be in the default. Two near-free diagnostics "
    "and a six-point protocol close the paper.",

    "The manuscript engages the journal's own conversation on reproducibility (Marwick, 2017) "
    "and on visibility networks (Brughmans, Keay, & Earl, 2015), and brings to it the testing "
    "literature of software engineering —metamorphic relations, mutation analysis, the oracle "
    "problem— which, to the author's knowledge, has not previously been applied to an "
    "archaeological geometric computation.",

    "The manuscript runs to about %s words of main text, with %d figures, %d tables and %d "
    "references; the abstract has %d words. It is a single-author work; the author declares no "
    "competing interests and no funding. In accordance with the journal's policy, the use of a "
    "large language model as a coding and drafting assistant is documented in the Methods "
    "section, and the author takes full responsibility for the content."
    % ("{:,}".format(n_cuerpo), n_fig, n_tab, n_refs, n_abs),

    "Yours faithfully,",
    "%s\n%s\n%s – ORCID %s" % (AUTOR, FILIACION, CORREO, ORCID),
]

with open(os.path.join(OUT, "2_COVER_LETTER.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n\n".join(CARTA) + "\n")

doc = Document()
sec = doc.sections[0]
sec.top_margin = sec.bottom_margin = Cm(2.5)
sec.left_margin = sec.right_margin = Cm(2.5)
st = doc.styles["Normal"]
st.font.name = "Arial"
st.font.size = Pt(10.5)
st.paragraph_format.space_after = Pt(8)
st.paragraph_format.line_spacing = 1.15
for i, par in enumerate(CARTA):
    for linea in par.split("\n"):
        p = doc.add_paragraph()
        p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if i in (0, len(CARTA) - 2, len(CARTA) - 1)
                       else WD_ALIGN_PARAGRAPH.JUSTIFY)
        r = p.add_run(linea)
        r.font.name = "Arial"
        r.font.size = Pt(10.5)
        if par.startswith("Yours") or i == len(CARTA) - 1:
            p.paragraph_format.space_after = Pt(2)
out_docx = os.path.join(OUT, "2_COVER_LETTER.docx")
doc.save(out_docx)
docmeta.limpiar(out_docx, autor=AUTOR, titulo="Cover letter - Journal of Archaeological Method and Theory")

print("Paquete -> %s" % OUT)
print("  manuscrito: %s palabras de cuerpo | resumen %d | figuras %d | tablas %d | referencias %d"
      % ("{:,}".format(n_cuerpo), n_abs, n_fig, n_tab, n_refs))
print("  ficheros:", sorted(os.listdir(OUT)))
