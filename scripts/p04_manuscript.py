# -*- coding: utf-8 -*-
"""
Genera el manuscrito en ingles, leyendo cada cifra de los JSON de resultados.

La disciplina es la del caso de estudio que este articulo describe: ningun
numero se escribe a mano. Los que proceden de un calculo se leen de
benchmark.json, calibracion.json y comparacion_motores.json; los estructurales
(la distancia critica de curvatura) se derivan aqui de las mismas constantes
que usa el motor.

Version para Journal of Archaeological Method and Theory (Springer) tras el
rechazo de mesa del JAS: revision de anonimo simple con autoria en el propio
manuscrito, resumen de 150 a 250 palabras, citas APA con coma, referencias
APA 7 con enlace DOI completo, pies «Fig. n», seccion de antecedentes sobre
incertidumbre de las cuencas visuales y correccion del software cientifico,
y «Statements and Declarations» antes de las referencias. El uso de un modelo
de lenguaje se documenta en Metodos, como pide la politica editorial.

Salida: manuscript_silent_failures.docx
"""
import json
import math
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Mm, Pt, RGBColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docmeta
from los_engine import R_EFF

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
FIG = os.path.join(RES, "figuras")
OUT = os.path.join(BASE, "manuscript_silent_failures.docx")

BEN = json.load(open(os.path.join(RES, "benchmark.json"), encoding="utf-8"))
CAL = json.load(open(os.path.join(RES, "calibracion.json"), encoding="utf-8"))
FMETA = json.load(open(os.path.join(FIG, "meta.json"), encoding="utf-8"))
MOT = json.load(open(os.path.join(RES, "comparacion_motores.json"), encoding="utf-8"))

# El caso de campo: las tres z citadas se leen de los ficheros del deposito,
# copiados en data/caso_titicaca, no se escriben a mano.
_CT = os.path.join(BASE, "data", "caso_titicaca")


def _cz(fn):
    return json.load(open(os.path.join(_CT, fn), encoding="utf-8"))["por_alcance"]["5000"]["z"]


Z_CAMPO_OK = _cz("nulo_rigido.json")                 # el contraste corregido
Z_CAMPO_AGUA = _cz("nulo_rigido_sin_mascara.json")   # el contraejemplo del agua
Z_CAMPO_RECORTE = _cz("nulo_rigido_n300.json")       # el contraejemplo del recorte

# ------------------------------------------------------------------ derivados
D_CRIT_KM = math.sqrt(8.0 * R_EFF * (1.7 + 3.0) / 2.0) / 1000.0
N_CASOS = len(BEN["motor_correcto"]["casos"])
N_PROPS = len(BEN["motor_correcto"]["propiedades"])
N_TESTS = BEN["motor_correcto"]["pruebas"]
MUT = BEN["mutantes"]
DETECTADOS = [d for d, v in MUT.items() if v["detectado"]]
EQUIVALENTES = [d for d, v in MUT.items() if v.get("equivalente")]
CFG = CAL["config"]
R_ = CFG["replicas"]
RESU = CAL["resumen"]
POT_TEO = RESU["potencia_teorica_S1_correcto"]
MEC = RESU["mecanismo_recorte"]
DIAG = RESU["diagnosticos"]
_G = MOT["motores"]["GDAL gdal_viewshed"]
_R = MOT["motores"]["GRASS r.viewshed"]
N_DISC = MOT["discrepancia_entre_motores_de_fabrica"]["casos"]
N_GDAL_FALLA = _G["direccion"]["declara_tapado_lo_visible"]
N_GRASS_FALLA = _R["direccion"]["declara_visible_lo_tapado"]

DOI_CASO = "10.5281/zenodo.22176260"
DOI_ESTE = "10.5281/zenodo.22242923"
AUTOR = "Milton Vladimir Mamani Calisaya"
FILIACION = "Universidad Nacional del Altiplano, Puno, Perú"
CORREO = "mmamanic@unap.edu.pe"
ORCID_A = "0000-0002-0676-0989"


def f(x, dec=2):
    return ("%%.%df" % dec) % x


def fz(x):
    """z con signo explicito, que es como se leen los contrastes."""
    return "%+.2f" % x


def pct(x, dec=0):
    return ("%%.%df" % dec) % (100.0 * x)


# ------------------------------------------------------------------ documento
# El lenguaje visual es el de una maqueta editorial sobria: una sola familia
# (Arial), jerarquia por tamano, versalitas e interletrado en los titulos,
# reglas finas en el gris calido de las figuras, tablas sin bordes verticales
# al modo booktabs, folio y cabecera. Nada decorativo: todo lo que se ve
# ordena la lectura.
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

TINTA = RGBColor(0x21, 0x1F, 0x1C)       # casi negro, calido
TINTA_SUAVE = RGBColor(0x4A, 0x46, 0x3F) # gris calido de los rotulos
GRIS_PIE = RGBColor(0x6E, 0x6A, 0x62)    # pies de figura y folio
REGLA = "55524B"                          # el gris de los bordes de las figuras
CREMA = "F2EFE9"                          # el relleno de las cajas del pipeline

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.top_margin = sec.bottom_margin = Cm(2.5)
sec.left_margin = sec.right_margin = Cm(2.5)

st = doc.styles["Normal"]
st.font.name = "Arial"
st.font.size = Pt(10)
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.15


def _interletrado(r, veintavos=14):
    rPr = r._r.get_or_add_rPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:val"), str(veintavos))
    rPr.append(sp)


def _borde_parrafo(p, lado="left", sz=14, color=REGLA, espacio=10):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:" + lado)
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), str(sz))
    b.set(qn("w:space"), str(espacio))
    b.set(qn("w:color"), color)
    pBdr.append(b)
    pPr.append(pBdr)


def _sombrea(celda, color=CREMA):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), color)
    celda._tc.get_or_add_tcPr().append(sh)


def _borde_celda(celda, lados):
    tcPr = celda._tc.get_or_add_tcPr()
    tb = OxmlElement("w:tcBorders")
    for lado in ("top", "left", "bottom", "right"):
        b = OxmlElement("w:" + lado)
        if lado in lados:
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), str(lados[lado]))
            b.set(qn("w:color"), REGLA)
        else:
            b.set(qn("w:val"), "nil")
        tb.append(b)
    tcPr.append(tb)


def run(p, t, size=10, bold=False, italic=False, color=None, caps=False, track=0):
    r = p.add_run(t)
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = color if color is not None else TINTA
    if caps:
        r.font.small_caps = True
    if track:
        _interletrado(r, track)
    return r


def P(t, size=10, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
      before=0, after=6, color=None, caps=False, track=0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.15
    run(p, t, size, bold, italic, color=color, caps=caps, track=track)
    return p


def h1(t):
    return P(t, 11.5, True, align=WD_ALIGN_PARAGRAPH.LEFT, before=16, after=6,
             caps=True, track=16)


def h2(t):
    return P(t, 10.5, True, align=WD_ALIGN_PARAGRAPH.LEFT, before=10, after=4,
             color=TINTA_SUAVE)


def etiqueta(t, after=3):
    return P(t, 10, True, align=WD_ALIGN_PARAGRAPH.LEFT, after=after,
             caps=True, track=14, color=TINTA_SUAVE)


def figure(fn, label, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(os.path.join(FIG, fn), width=Mm(155))
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    q.paragraph_format.space_after = Pt(12)
    q.paragraph_format.line_spacing = 1.1
    run(q, label + " ", 9, bold=True)
    run(q, caption, 9, color=GRIS_PIE)


def table(label, caption, cols, rows, widths=None):
    q = doc.add_paragraph()
    q.paragraph_format.space_before = Pt(10)
    q.paragraph_format.space_after = Pt(4)
    q.paragraph_format.line_spacing = 1.1
    run(q, label + " ", 9, bold=True)
    run(q, caption, 9, color=GRIS_PIE)
    t = doc.add_table(rows=1 + len(rows), cols=len(cols))
    t.alignment = 1
    for j, c in enumerate(cols):
        cell = t.rows[0].cells[j]
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(cell.paragraphs[0], c, 8.5, bold=True)
        _sombrea(cell)
        _borde_celda(cell, {"top": 12, "bottom": 6})
    ultima = len(rows) - 1
    for i, fila in enumerate(rows):
        for j, v in enumerate(fila):
            cell = t.rows[1 + i].cells[j]
            cell.paragraphs[0].alignment = (WD_ALIGN_PARAGRAPH.LEFT if j == 0
                                            else WD_ALIGN_PARAGRAPH.CENTER)
            run(cell.paragraphs[0], str(v), 8.5)
            _borde_celda(cell, {"bottom": 12} if i == ultima else {})
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def _campo_pagina(p):
    """Numero de pagina como campo de Word: la numeracion automatica que pide Springer."""
    for tag, extra in (("fldChar", {"w:fldCharType": "begin"}),
                       ("instrText", None),
                       ("fldChar", {"w:fldCharType": "end"})):
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        rf = OxmlElement("w:rFonts"); rf.set(qn("w:ascii"), "Arial"); rPr.append(rf)
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "17"); rPr.append(sz)
        colr = OxmlElement("w:color"); colr.set(qn("w:val"), "6E6A62"); rPr.append(colr)
        r.append(rPr)
        e = OxmlElement("w:" + tag)
        if extra:
            for k, v in extra.items():
                e.set(qn(k), v)
        if tag == "instrText":
            e.set(qn("xml:space"), "preserve")
            e.text = " PAGE "
        r.append(e)
        p._p.append(r)


def cabecera_y_folio():
    ph = sec.header.paragraphs[0]
    ph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run(ph, "Silent failures in archaeological visibility analysis", 8,
        color=GRIS_PIE, caps=True, track=12)
    pf = sec.footer.paragraphs[0]
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _campo_pagina(pf)


cabecera_y_folio()

# numeracion continua de lineas: facilita la revision y no la impide ninguna norma
_ln = OxmlElement("w:lnNumType")
_ln.set(qn("w:countBy"), "1")
_ln.set(qn("w:restart"), "continuous")
sec._sectPr.append(_ln)

# ================================================================== title page
P("Reproducible and wrong", 19, True, align=WD_ALIGN_PARAGRAPH.CENTER,
  before=10, after=2, track=10)
P("Silent failures in archaeological visibility analysis and a benchmark to catch them",
  12, align=WD_ALIGN_PARAGRAPH.CENTER, after=0, color=TINTA_SUAVE, italic=True)
_regla = doc.add_paragraph()
_regla.paragraph_format.space_before = Pt(10)
_regla.paragraph_format.space_after = Pt(12)
_borde_parrafo(_regla, "bottom", sz=8, espacio=1)

# Bloque de autoria: la revista revisa en anonimo simple y pide la portada
# dentro del manuscrito (nombre, filiacion, correo de correspondencia, ORCID).
P(AUTOR, 11, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
P(FILIACION, 9.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, color=TINTA_SUAVE)
P("Corresponding author: %s  ·  ORCID https://orcid.org/%s" % (CORREO, ORCID_A),
  9, align=WD_ALIGN_PARAGRAPH.CENTER, after=16, color=TINTA_SUAVE)

etiqueta("Abstract")
ABSTRACT = (
    "Computational reproducibility guarantees that an analysis can be re-run and will return the "
    "same result. It does not guarantee that the result is true: a reproducible pipeline reproduces "
    "its errors faithfully. This paper characterises a class of defects in archaeological visibility "
    "analysis that crash nothing, produce plausible output, survive both peer review and "
    "re-execution, and invert or erase the conclusion of the study containing them. Three members "
    "were documented in a recent Titicaca-basin intervisibility study and are reproduced here under "
    "controlled conditions. Two instruments are presented: an executable benchmark for line-of-sight "
    "engines, with %d terrain cases whose expectations are derived rather than written by hand and "
    "%d behavioural properties, whose own adequacy is measured by mutation analysis; and a "
    "synthetic-landscape laboratory in which the truth is known by construction. Sampling null "
    "placements over water destroys statistical power (%s %% against a ceiling of %s %%) without "
    "raising false positives; a tightly cropped sampling region biases the contrast in a direction "
    "set by the alignment between site configuration and terrain grain (Spearman rho = %s) and is "
    "invisible to a marginal calibration audit. Two near-free diagnostics flag both. Put to the same "
    "benchmark, GDAL and GRASS, both reached through QGIS, pass every case when configured "
    "deliberately yet contradict each other on %d of %d cases at their shipped defaults, failing in "
    "opposite directions. Reproducibility certifies the transport of a computation; validation "
    "certifies its content. The discipline needs both."
    % (N_CASOS, N_PROPS, pct(RESU["S1"]["agua"]["rechazo"]), pct(POT_TEO),
       f(MEC["spearman_desalineacion"], 2), N_DISC, N_CASOS))
assert 150 <= len(ABSTRACT.split()) <= 250, "resumen de %d palabras" % len(ABSTRACT.split())
P(ABSTRACT, after=8, size=9.5)
_borde_parrafo(doc.paragraphs[-1], "left")
doc.paragraphs[-1].paragraph_format.left_indent = Cm(0.35)

etiqueta("Keywords")
P("viewshed analysis; software validation; mutation testing; computational reproducibility; "
  "null models; geographic information systems", after=18, size=9.5, italic=True,
  color=TINTA_SUAVE)

# ================================================================ introduction
h1("1. Introduction")

P("Archaeology has spent a decade building the case for computational reproducibility. The argument "
  "is settled: analyses should ship their code and data, be version-controlled, and re-run from top "
  "to bottom on demand (Marwick, 2017; Peng, 2011; Sandve et al., 2013). The case was made in this "
  "journal, with a worked example, and it has since reshaped how archaeological science is done and "
  "reported (Schmidt & Marwick, 2020). This paper is about what that programme, on its own, cannot "
  "deliver. Re-running an analysis verifies that the code produces the reported numbers; it says "
  "nothing about whether the numbers are right. A pipeline with an inverted sign is perfectly "
  "reproducible. It reproduces the inverted sign.")

P("The distinction has become sharper as the reproducibility agenda has matured. Surveys of "
  "scientists find that most have failed to reproduce someone else's results and many their own "
  "(Baker, 2016); an audit of a journal with a code-sharing policy could obtain and run the code "
  "behind fewer than half of the sampled articles (Stodden et al., 2018); and reviews of the "
  "computing literature catalogue the many layers —environment, dependencies, numerical libraries— "
  "at which a re-execution can quietly diverge (Ivie & Thain, 2018). Geography and geographic "
  "information science have taken up the agenda for spatial analysis specifically (Brunsdon, 2016; "
  "Nüst & Pebesma, 2021), and Kedron et al. (2021) have drawn the useful distinction between "
  "reproducibility —the same data and code return the same result— and replicability —new data "
  "return the same finding. Neither, they note, is validity. A study can be reproducible, replicable "
  "and wrong, if the defect lives in the shared procedure.")

P("The defects that matter here are of a specific kind. A sign error in a data-processing script "
  "forced the retraction of five protein-structure papers, three of them in Science (Miller, 2006). "
  "A spreadsheet error silently shaped a decade of fiscal policy before anyone re-derived the "
  "numbers (Herndon et al., 2014). Merali (2010) and Soergel (2015) argue that software faults of "
  "this kind are common enough to undermine results across computational science generally, and "
  "Hatton and Roberts (1994) had already shown, by handing the same seismic data to nine "
  "independent processing packages, that the disagreement between them exceeded the signal the "
  "analysis was meant to detect. What makes these cases instructive is not that software failed but "
  "how it failed: no crash, no warning, output of entirely plausible appearance.")

P("Archaeological visibility analysis —a methodological tradition reviewed by Lake and Woodman "
  "(2003) and critically examined by Wheatley and Gillings (2000) and Gillings (2015, 2017)— is "
  "unusually exposed to this failure mode. A viewshed or intervisibility computation returns maps "
  "and networks that look reasonable under almost any defect, and there is no ground truth on real "
  "terrain against which to notice that they are wrong; Fisher (1993) showed three decades ago that "
  "independent implementations of the same viewshed disagree substantially without any of them "
  "being obviously broken, and Riggs and Dean (2007) traced such disagreements to undeclared "
  "implementation decisions. Reviewers see results, not code, so review does not catch the defect. "
  "Reproduction re-executes the same code, so reproduction does not catch it either. The defect "
  "passes through every control the discipline currently operates.")

P("A recent intervisibility study of 180 archaeological sites in the Titicaca basin documented "
  "three such defects encountered —and corrected— during its own analysis (Mamani Calisaya et al., "
  "2026). The sign of the Earth-curvature correction was inverted, which renders the Earth concave "
  "and lets no relief block any long-range view. The elevation model assigned a constant elevation "
  "to the lake, a perfect plane covering 30.6 %% of the study area that blocks nothing and inflated "
  "the null model until a real effect vanished (z = %s against z = %s once masked). And a tightly "
  "fitted raster crop admitted only 244 of 360 orientations of the rigid null model, inflating the "
  "contrast from z = %s to z = %s. None of the three produced any visible failure. Each was found "
  "by accident or by a purpose-built check, not by inspection of results."
  % (fz(Z_CAMPO_AGUA), fz(Z_CAMPO_OK), fz(Z_CAMPO_OK), fz(Z_CAMPO_RECORTE)))

P("This paper treats that episode as a specimen and builds the instruments the discipline lacks. "
  "Its contributions are: (1) a characterisation of the silent failure class and a two-level "
  "taxonomy —defects of the geometric engine versus defects of the analysis design— with seven "
  "concrete, field-documented or field-plausible members; (2) an executable benchmark for "
  "line-of-sight engines whose adequacy is itself measured, by mutation analysis, rather than "
  "asserted; (3) a synthetic-landscape laboratory in which the truth is known by construction, so "
  "the damage each design defect does to statistical inference is measured exactly; (4) a "
  "measurement of two production engines in everyday archaeological use, GDAL and GRASS, against "
  "the same benchmark, which shows that the defect need not be in the code at all; and (5) two "
  "diagnostics and a six-point protocol that detect the documented defects at negligible cost, "
  "before any real terrain is touched.")

# ================================================================= background
h1("2. Background")
h2("2.1. Uncertainty in viewshed computation")
P("The archaeological literature has known for thirty years that a viewshed is not a fact about "
  "the terrain but an output of a procedure. Fisher (1993) computed the same viewshed with several "
  "GIS packages and found that the areas they returned differed by margins that no analyst would "
  "tolerate in a measurement, without any package being demonstrably wrong; he called this "
  "algorithm and implementation uncertainty and distinguished it from the uncertainty of the "
  "elevation model itself. Nackaerts et al. (1999) assessed probabilistic visibilities against field "
  "observation, and Riggs and Dean (2007) went further into the mechanism, attributing "
  "inconsistencies between predicted viewsheds to specific implementation choices —how the terrain "
  "profile is interpolated, how the observer's own cell is treated, whether curvature is applied— "
  "that are rarely reported and, when reported, rarely justified. Kormann and Lock (2014) examined "
  "the effect of curvature and refraction on archaeological visibility studies and concluded that "
  "at ranges of several kilometres both terms change the result, which is the regime in which the "
  "field defects reproduced here operate.")
P("The response of the archaeological community to this uncertainty has been, in the main, to "
  "model it rather than to eliminate it. Fuzzy and probabilistic viewsheds propagate elevation "
  "error into a graded map; multiple-viewshed and total-viewshed approaches average over "
  "observers; and the network turn —treating intervisibility as a graph and modelling the "
  "dependence between its edges with exponential random graph models (Brughmans et al., 2015; "
  "Brughmans & Brandes, 2017)— moves the inference to a level where individual lines of sight "
  "matter less. Lake et al. (1998) showed early on that the software itself could be tailored to "
  "the archaeological question, and Čučković (2016) published the QGIS plug-in through which much "
  "of the community now computes visibility; Ducke (2012) argued that free and open-source software "
  "is the only route by which an analysis can be audited down to the algorithm. What none of this "
  "work provides is a way to decide whether a given engine, with a given configuration, is correct. "
  "Fisher's disagreement is treated as a property of the operation, when much of it is the "
  "signature of defects that a benchmark could attribute to one implementation or the other.")
P("The design level has received the same kind of attention. Lake and Woodman (2003) and Wheatley "
  "and Gillings (2000) established that the null model against which an observed visibility pattern "
  "is tested decides the result as much as the pattern does, and that random points drawn from the "
  "whole landscape are the wrong comparison when sites share topographic traits. The field study "
  "behind this paper followed that advice and still went wrong twice at the design level, in ways "
  "the advice does not anticipate: not in which null to use, but in where the null was allowed to "
  "sample. That is the gap the landscape laboratory of Section 3.4 addresses.")

h2("2.2. Correctness of scientific software and the oracle problem")
P("Software engineering has a name for the difficulty at the centre of this paper. Testing a "
  "program requires an oracle —a way of knowing what the correct output is— and scientific software "
  "is written precisely to compute answers that nobody knows in advance. Kanewala and Bieman (2014) "
  "reviewed the literature on testing scientific software and found the oracle problem to be its "
  "defining obstacle; Hatton (1997) reported experiments in which mature scientific codes, given "
  "identical inputs, produced results whose spread grew with every stage of the computation. The "
  "field's answers to the oracle problem are three, and this paper applies all of them to visibility "
  "analysis. The first is to derive expectations from theory where a closed form exists, so that "
  "the test knows the answer for a reason and not by assertion. The second is metamorphic testing "
  "(Chen et al., 2018; Segura et al., 2016): instead of asking what the output should be, ask how "
  "the output must change when the input changes in a known way —raising the observer can never "
  "remove a line of sight— and check the relation over many random inputs, in the manner of "
  "property-based testing (Claessen & Hughes, 2000). A defective engine cannot satisfy such a "
  "relation by coincidence, because there is no specific case to be accidentally right about.")
P("The third answer measures the tests themselves. A suite that the correct program passes proves "
  "little; the question is whether it would fail a defective one. Mutation analysis (DeMillo et al., "
  "1978; Jia & Harman, 2011) answers exactly this by injecting known defects and counting how many "
  "the suite detects, and it carries a subtlety that matters here: some mutations do not change "
  "observable behaviour at all, and a suite must not be blamed for failing to detect what cannot be "
  "detected. None of these techniques is new to software engineering. What is new is their "
  "application to a geometric computation in archaeology, and the finding —reported in Section "
  "4.2— that the expectations archaeologists write by hand fail at the same rate, and for the same "
  "reasons, as the code they are meant to check.")

h2("2.3. The failure class")
P("A silent failure, as the term is used here, is a defect with four properties: it raises no "
  "error and produces no visibly malformed output; its output is plausible and interpretable, "
  "statistics included; it survives both peer review (which sees results, not code) and "
  "computational reproduction (which re-executes the defect); and it changes the substantive "
  "conclusion of the study. The last clause is what separates a silent failure from a tolerable "
  "approximation: the defects studied here do not perturb the result, they invert or erase it.")

P("Two levels must be distinguished, because they demand different instruments. Engine defects "
  "live in the geometric computation itself: a wrong sign, a missing correction, an ill-chosen "
  "default, a sampling shortcut. Design defects live above a perfectly correct engine, in how the "
  "null model is constructed and where it is allowed to sample. Table 1 lists the seven defects "
  "treated in this paper. Every engine defect is either documented in the field episode or is a "
  "default that mainstream software makes easy —and Section 4.5 shows that two of them are the "
  "literal defaults of the software most archaeologists run; both design defects are documented.")

table("Table 1.", "The seven defects studied. The first five are injected into the line-of-sight "
      "engine; the last two into the design of the null-model contrast. ‘Documented’ "
      "means observed and quantified in the Titicaca field study; ‘shipped default’ means "
      "the behaviour of a production engine at its factory settings (Section 4.5).",
      ["Defect", "Level", "Mechanism", "Status"],
      [["Curvature subtracted", "engine", "Earth rendered concave; nothing blocks at range", "documented"],
       ["Curvature omitted", "engine", "defensible below a few km, wrong beyond", "shipped default (GRASS)"],
       ["Target height zero", "engine", "monument treated as a point on the ground", "shipped default (GDAL)"],
       ["Endpoints included", "engine", "observer blocks itself on its own relief", "equivalent (see 4.1)"],
       ["Coarse profile sampling", "engine", "narrow barriers fall between samples", "plausible shortcut"],
       ["Water left unmasked", "design", "a flat lake that blocks nothing feeds the null", "documented"],
       ["Tightly cropped region", "design", "null placements lose orientations that do not fit", "documented"]])

# ==================================================================== methods
h1("3. Materials and methods")
P("The architecture is summarised in Fig. 1. Two instruments answer two different questions "
  "—whether the geometry is right, and whether the inference is right— and converge on one "
  "rule: only a validated engine and a diagnosed design touch real terrain.")
figure("fig_pipeline.png", "Fig. 1",
       "The validation pipeline. Left, the engine level: a line-of-sight engine with five "
       "switchable defects is run against a benchmark of terrain cases with derived expectations "
       "and behavioural properties, and the benchmark itself is audited by mutation analysis. "
       "Right, the design level: synthetic landscapes where the truth is known by construction "
       "measure what each design defect does to calibration and power. Both levels feed two "
       "diagnostics that any real study can print before computing a single line of sight.")

h2("3.1. A line-of-sight engine with switchable defects")
P("The reference engine evaluates the line of sight between two cells of a digital elevation "
  "model by sampling the intervening terrain at one sample per cell and testing whether it rises "
  "above the straight line joining observer and target. Earth curvature and atmospheric refraction "
  "are combined in an effective radius R/(1−k) with k = 0.13; written with respect to the chord "
  "between the endpoints, the correction term d(D−d)/2R is added to the intervening terrain, "
  "because seen from that chord the Earth bulges between the endpoints and the bulge vanishes at "
  "them. Subtracting the term —which is what the customary phrase ‘drop due to "
  "curvature’ suggests— is the first defect. Each of the five engine defects of Table 1 "
  "can be switched on by name, which is what makes the adequacy of the benchmark measurable "
  "(Section 3.3). The engine and every experiment below depend only on NumPy.")

h2("3.2. Test cases with derived expectations, and behavioural properties")
P("The benchmark has two parts. The first is %d terrain cases whose correct answer is known in "
  "advance: a plane at short range, barriers that must and must not block, a depression that can "
  "never block, observer and target standing on their own summits, and planes bracketing the "
  "critical distance at which curvature alone severs the view. That distance is not written by "
  "hand: over a plane, the mid-path bulge D²/8R equals the mean sight-line height "
  "(hₒ+hₜ)/2 at D = %s km for the default heights, and the cases probe both sides of the "
  "derived value. The reason for this discipline appears in Section 4.2." % (N_CASOS, f(D_CRIT_KM, 1)))
P("The second part is %d behavioural properties checked over hundreds of random rugged terrains: "
  "visibility is reciprocal; raising the observer never removes visibility; over a plane, "
  "visibility lost to curvature never returns with further distance; raising a barrier never "
  "unblocks a view. These are metamorphic relations in the sense of Section 2.2 (Chen et al., "
  "2018; Segura et al., 2016), and their value is that a defective engine cannot satisfy them by "
  "coincidence, because there is no specific case to be accidentally right about (Claessen & "
  "Hughes, 2000)." % N_PROPS)

h2("3.3. Mutation analysis: measuring the benchmark itself")
P("A validation suite that passes the correct engine proves little; the question is whether it "
  "would fail a defective one. Mutation analysis answers exactly this (DeMillo et al., 1978; Jia & "
  "Harman, 2011): each defect of Section 3.1 is switched on in turn and the full benchmark is run "
  "against the mutated engine. A defect that no test detects marks a hole in the benchmark —unless "
  "the mutation does not alter observable behaviour at all, in which case it is an equivalent "
  "mutant and detecting it is impossible in principle. The two situations are distinguished "
  "empirically, by sweeping the mutant against the reference engine over thousands of random "
  "terrain pairs and endpoint configurations.")

h2("3.4. A landscape laboratory with ground truth by construction")
P("Engine defects can be caught by geometry. Design defects cannot: they operate above a correct "
  "engine, and on real terrain there is no way to know what the contrast should have concluded. "
  "The laboratory therefore manufactures landscapes where the truth is known exactly. Each "
  "replicate generates an anisotropic synthetic terrain —ridges with a dominant, randomised "
  "grain direction— with a lake occupying about a quarter of the map, built the way real "
  "elevation models build lakes: by flooding a basin to a constant elevation (Fig. 3a). An "
  "elongated cloud of %d sites is then placed under two scenarios. In scenario S0 the cloud is "
  "placed by the very rules the rigid null model uses to place its own draws; observed and null "
  "placements are then exchangeable, and the p-value of a correct contrast is uniform by symmetry "
  "—exactly, up to ties in the discrete density, which can only make the test conservative. Every "
  "measured departure from uniformity is therefore attributable to the procedure, not to chance. "
  "In scenario S1 the cloud is placed at the best of %d random placements, which makes ‘sited "
  "where it sees more than the same configuration would elsewhere’ true by construction; "
  "the theoretical power of a correct contrast follows from rank symmetry and is computed "
  "alongside the experiment." % (32, CFG["k_mejor"]))
P("Each replicate then runs the same contrast three times on identical data: with the correct "
  "design, with null placements allowed onto the water, and with the null sampling region cropped "
  "to the bounding box of the observed cloud plus %d cells. The design is paired: any difference "
  "between procedures is attributable to the defect alone. %d replicates were run, each with %d "
  "null placements per contrast." % (CFG["margen_ajustado_celdas"], R_, CFG["n_null"]))

h2("3.5. Diagnostics")
P("Two checks are computed in every run, neither requiring ground truth. D1: the fraction of "
  "accepted null placements with at least one site on water —in a sound design, identically "
  "zero. D2: the fraction of the 360 placement orientations that fit geometrically inside the "
  "sampling region (Fig. 3b–c) —in a sound design, 100 %. Both are near-free to compute, and "
  "either would have flagged its corresponding field defect before a single line of sight was "
  "calculated.")

h2("3.6. Production engines under the same benchmark")
P("The instruments above are built around an engine written for this study, which proves that the "
  "benchmark can detect defects but says nothing about the software archaeology actually runs. "
  "The %d terrain cases were therefore materialised as small georeferenced rasters and submitted, "
  "through the QGIS processing framework, to two production engines: gdal_viewshed, the GDAL "
  "implementation exposed in the QGIS toolbox (QGIS %s), and r.viewshed of GRASS GIS %s. Each "
  "engine was run twice on every case. The first run set every parameter to the value this study "
  "uses —observer 1.7 m, target 3.0 m, curvature and refraction through the same coefficient "
  "1−k— and the second left every parameter the engine ships with, which is what an analyst who "
  "opens the tool and presses Run obtains. The verdict of each run was read back from the output "
  "raster at the target cell and compared with the derived expectation of the case. Nothing in the "
  "benchmark was adapted to either engine: the cases are the same files the reference engine is "
  "tested on." % (N_CASOS, _G["version"].replace("QGIS ", ""), _R["version"]))

h2("3.7. Software and tooling")
P("Everything depends on NumPy alone, with Matplotlib for the figures and python-docx for the "
  "manuscript, which is generated from the result files so that no number in the text is typed by "
  "hand; an automated audit, deposited with the code, checks every figure cited against the file "
  "it comes from. In accordance with the journal's policy on large language models, the author "
  "declares that Claude (Anthropic) was used as a coding and drafting assistant during the "
  "development of the analysis code, the figures and the text. Every line of code was reviewed by "
  "the author and is exercised by the deposited benchmark and audits, every result was recomputed "
  "from the deposited scripts, and the author takes full responsibility for the content of the "
  "article.")

# ==================================================================== results
h1("4. Results")

h2("4.1. The benchmark and its mutation matrix")
P("The reference engine passes all %d tests. Table 2 gives the mutation matrix. Every defect with "
  "observable consequences is detected, most by several independent tests. The exception is "
  "instructive: including the endpoint cells in the blocking test —a plausible off-by-one— "
  "turns out to be behaviourally equivalent to the correct engine, because the sight line is "
  "anchored at terrain-plus-height on both endpoints and by construction can never be exceeded "
  "there. The sweep of Section 3.3 found no difference in any of %s paired evaluations. "
  "Reporting this matters: mutation analysis without an equivalence check would count it as a "
  "hole in the benchmark, making the suite look weaker than it is (Jia & Harman, 2011). "
  "Fig. 2 dissects two of the killed mutants on single terrain profiles: in each panel the "
  "defective verdict is exactly as visually plausible as the correct one, which is the failure "
  "class in one image."
  % (N_TESTS, "{:,}".format(MUT["extremos_incluidos"]["comparaciones_equivalencia"])))

table("Table 2.", "Mutation matrix: for each injected engine defect, how many of the %d benchmark "
      "tests detect it, and the first test to do so." % N_TESTS,
      ["Injected defect", "Detected", "Tests failing", "First failing test"],
      [[d, ("yes" if MUT[d]["detectado"] else
            ("equivalent" if MUT[d].get("equivalente") else "NO")),
        "%d / %d" % (MUT[d]["pruebas_que_saltan"], N_TESTS),
        (MUT[d]["cuales"][0] if MUT[d]["cuales"] else "—")]
       for d in MUT])

figure("fig_anatomia.png", "Fig. 2",
       "Anatomy of a silent failure. (a) The correct engine finds this %s km line of sight blocked: "
       "with curvature and refraction applied, the deciding relief rises barely two metres above "
       "the line. (b) The same pair with the curvature term subtracted instead of added: the "
       "terrain sags away from the chord and the view is clear. Both panels look entirely "
       "plausible in isolation. (c) Coarse profile sampling: an 80 m barrier one cell wide falls "
       "between two of ten samples and the engine reports a clear view. (d) The same terrain as "
       "(a) at short range: every variant agrees, which is why small study areas cannot expose "
       "the defect." % f(FMETA["fig1_km"], 1))

h2("4.2. Hand-written expectations fail the same way code does")
P("Five test expectations written by hand during this research were wrong, and all five for the "
  "same reason. In the field study, two of the twelve validation cases initially encoded "
  "expectations that forgot the curvature term the validation existed to check. In the present "
  "benchmark, three cases were first written at 12 km —beyond the derived critical distance of "
  "%s km— where curvature alone already blocks a plane, so the feature each case claimed to "
  "test never decided the outcome. Two of the three were caught because the correct engine failed "
  "them. The third passed the correct engine and kept passing, for the wrong reason, until the "
  "mutation matrix showed the coarse-sampling defect surviving a test named after the very "
  "barrier it should have missed. The test was measuring curvature, not sampling." % f(D_CRIT_KM, 1))
P("The episode is small and, precisely for that reason, representative: expectations are code, "
  "they fail like code, and they fail silently like code. Two practices follow. Expectations "
  "should be derived from theory wherever a closed form exists —the critical-distance formula "
  "replaced all five hand-written numbers— and the test suite itself should be audited by "
  "mutation analysis, which is the only instrument in this study that caught a test passing for "
  "the wrong reason.")

h2("4.3. What the design defects do to inference")
P("Table 3 and Fig. 4 give the laboratory results. The correct procedure behaves exactly as "
  "the exchangeability argument requires: under S0 its rejection rate is %s %% (95 %% CI "
  "%s–%s %%) at α = 0.05 and its p-values are compatible with uniformity "
  "(Kolmogorov–Smirnov p = %s); under S1 its power is %s %% against a theoretical ceiling of "
  "%s %%. The laboratory, in other words, is calibrated —which is what entitles it to measure "
  "the defects."
  % (pct(RESU["S0"]["correcto"]["rechazo"]),
     pct(RESU["S0"]["correcto"]["rechazo_ic95"][0]),
     pct(RESU["S0"]["correcto"]["rechazo_ic95"][1]),
     f(RESU["S0"]["correcto"]["ks_p_uniforme"], 3),
     pct(RESU["S1"]["correcto"]["rechazo"]), pct(POT_TEO)))

P("Letting the null sample the lake does not inflate the false-positive rate; it does something "
  "quieter and worse. Null placements on a perfect plane see almost everything, the null "
  "distribution shifts upward, and every real effect drowns: power collapses from %s %% to %s %%, "
  "with the mean z under a true effect falling from %s to %s. This is the mechanism that erased "
  "the field study's result before the lake was masked (z = %s against z = %s after). A "
  "defect of this polarity is the more dangerous for being ‘conservative’: it produces no "
  "spurious discoveries to retract, only true effects that were never seen."
  % (pct(RESU["S1"]["correcto"]["rechazo"]), pct(RESU["S1"]["agua"]["rechazo"]),
     f(RESU["S1"]["correcto"]["z_media"], 2), f(RESU["S1"]["agua"]["z_media"], 2),
     fz(Z_CAMPO_AGUA), fz(Z_CAMPO_OK)))

P("The tight crop is the more insidious result of the experiment, because it hides even from the "
  "audit one would design to find it. Marginally over landscapes its S0 p-values are "
  "indistinguishable from uniform (KS p = %s): a calibration study of the defective procedure "
  "alone would clear it. The paired design exposes what the marginal one cannot. On identical "
  "data, the crop shifts z relative to the correct procedure by ±%s (standard deviation; mean "
  "%s), and the direction of the shift is not noise: it correlates with the angle between the "
  "observed cloud and the terrain grain (Spearman rho = %s, p = %s; Fig. 4c). Clouds lying "
  "along the grain see their contrast inflated, clouds lying across it deflated, and the effects "
  "cancel only across an ensemble of landscapes that no analyst ever has —any single study "
  "sits at one point of Fig. 4c and inherits that point's bias. The field case is consistent "
  "with the laboratory's sign: a site cloud following the lakeshore corridor, and a crop that "
  "inflated its contrast from z = %s to z = %s. Under a real effect the cost is unambiguous: "
  "power falls from %s %% to %s %%."
  % (f(RESU["S0"]["recorte"]["ks_p_uniforme"], 3), f(MEC["dz_sd"], 2),
     f(MEC["dz_medio"], 2), f(MEC["spearman_desalineacion"], 2), f(MEC["p_spearman"], 4),
     fz(Z_CAMPO_OK), fz(Z_CAMPO_RECORTE),
     pct(RESU["S1"]["correcto"]["rechazo"]), pct(RESU["S1"]["recorte"]["rechazo"])))

table("Table 3.", "Calibration and power of the three procedures over %d paired replicates "
      "(%d null placements per contrast, α = 0.05). Under S0 a sound procedure rejects at "
      "α and its p-values are uniform; under S1 the theoretical power ceiling is %s %%."
      % (R_, CFG["n_null"], pct(POT_TEO)),
      ["Procedure", "S0: mean z (sd)", "S0: rejection", "S0: KS p(unif.)",
       "S1: mean z (sd)", "S1: power"],
      [[nombre,
        "%s (%s)" % (f(RESU["S0"][k]["z_media"], 2), f(RESU["S0"][k]["z_sd"], 2)),
        pct(RESU["S0"][k]["rechazo"]) + " %",
        f(RESU["S0"][k]["ks_p_uniforme"], 3),
        "%s (%s)" % (f(RESU["S1"][k]["z_media"], 2), f(RESU["S1"][k]["z_sd"], 2)),
        pct(RESU["S1"][k]["rechazo"]) + " %"]
       for k, nombre in (("correcto", "correct"), ("agua", "water unmasked"),
                         ("recorte", "tight crop"))])

figure("fig_laboratorio.png", "Fig. 3",
       "The landscape laboratory. (a) One synthetic replicate: anisotropic terrain with a lake "
       "built by flooding a basin to a constant elevation, the observed elongated cloud (red), "
       "three null placements (grey), and the tightly cropped sampling region (dashed). "
       "(b) Diagnostic D2 on the full region: all 360 orientations of the null placement fit. "
       "(c) The same diagnostic on the cropped region: only orientations near the cloud's own "
       "axis survive. The field-study analogue of this check would have read 244/360.")

figure("fig_consecuencias.png", "Fig. 4",
       "What the defects do to inference, over %d paired replicates. (a) Under no effect (S0), "
       "the empirical distribution of p-values: the correct procedure tracks the diagonal "
       "(uniform, as exchangeability requires); water-unmasked collapses towards p = 1; the tight "
       "crop also tracks the diagonal —marginally the defect is invisible, and panel (c) shows "
       "where it hides. (b) Under a real effect (S1), z by procedure, with "
       "empirical power against the theoretical ceiling. (c) The crop's paired z-shift against "
       "the misalignment between cloud and terrain grain: the direction of the bias is a property "
       "of the landscape, not of the data." % R_)

h2("4.4. The diagnostics flag both defects")
P("Across all replicates, %s %% of the defective water-run null placements touched water "
  "(diagnostic D1; the sound design scores zero by construction), and the cropped sampling region "
  "admitted on average %s %% of the 360 orientations against %s %% for the full region "
  "(diagnostic D2). Neither check needs ground truth, both cost microseconds, and either one "
  "prints a number that no analyst would wave through."
  % (pct(DIAG["agua_nulos_que_pisan_media"]), pct(DIAG["cobertura_recorte_S0_media"]),
     pct(DIAG["cobertura_completa_media"])))

h2("4.5. Two engines in everyday use, measured against the same benchmark")
P("Table 4 gives the outcome of the runs described in Section 3.6. Configured deliberately, both "
  "engines are correct: each passes all %d cases, including the derived curvature thresholds. The "
  "geometry of widely used software is not the problem. Left at its factory settings, however, "
  "each reproduces a defect from Table 1. GDAL defaults to a target height of zero —the "
  "‘target height zero’ defect, which Table 1 lists as a plausible default and which "
  "turns out to be the literal default— and fails %d of the %d cases, every one of them by "
  "declaring blocked what is visible. A 30 m monument behind a 12 m rise disappears. GRASS does "
  "not apply the Earth-curvature correction unless the -c flag is passed, and fails %d cases in "
  "the opposite direction, declaring visible what is blocked: with its shipped settings it reports "
  "a clear line of sight across 40 km of flat terrain, beyond the geometric horizon."
  % (N_CASOS, N_GDAL_FALLA, N_CASOS, N_GRASS_FALLA))

P("The consequence is the quantity Fisher (1993) described but could not attribute. On %d of the "
  "%d cases the two engines, at their defaults, return contradictory verdicts on identical "
  "terrain: an intervisibility study reaches opposite conclusions depending on which QGIS menu "
  "entry the analyst chose, and nothing in either output marks the disagreement. The defects "
  "are not in the code, which is correct in both; they are in the defaults, which are silent. "
  "This is also why a benchmark is the right instrument: it is the only one of the controls "
  "considered here that distinguishes a correct engine from a correct engine badly configured, "
  "and it turns the inter-implementation disagreement of Section 2.1 from a property of the "
  "operation into a list of attributable causes." % (N_DISC, N_CASOS))

table("Table 4.",
      "Two production viewshed engines against the %d benchmark cases, run with the "
      "parameters of this study and with the values they ship with." % N_CASOS,
      ["Engine", "Configured", "As shipped", "Default that differs",
       "Direction of failure"],
      [["GDAL gdal_viewshed (%s)" % _G["version"], _G["correcto"], _G["de_fabrica"],
        "target height = 0", "blocks the visible"],
       ["GRASS r.viewshed %s" % _R["version"], _R["correcto"], _R["de_fabrica"],
        "curvature off unless -c", "sees the blocked"]],
      widths=[58, 22, 22, 40, 34])

# ================================================================== discussion
h1("5. Discussion")
h2("5.1. Six practices")
P("The instruments presented here are cheap, and the failures they target are not hypothetical: "
  "all three field-documented defects pass silently through review and reproduction, and two of "
  "them singlehandedly decide the conclusion of a study. Six practices follow from the results, "
  "in rising order of novelty for the discipline.")
P("First, validate the geometric engine against synthetic terrains of known answer before it "
  "touches real terrain; on real terrain there is nothing to validate against (Fisher, 1993). "
  "Second, derive test expectations from theory wherever a closed form exists; Section 4.2 shows "
  "hand-written expectations failing at a rate —five of five errors traceable to one "
  "forgotten term— that no one would tolerate in the code under test. Third, audit the "
  "validation suite itself by mutation analysis, distinguishing equivalent mutants from holes; "
  "it is the only instrument here that caught a test passing for the wrong reason. Fourth, "
  "record and justify every parameter handed to a production engine: Section 4.5 shows that the "
  "defect need not live in the code at all, since two engines that each pass the whole benchmark "
  "disagree on %d of its %d cases when both are left at their own defaults. Fifth, diagnose the "
  "null model's sampler directly: placement validity (D1) and orientation coverage (D2) "
  "would have caught both design defects at the cost of two printed numbers. Sixth, publish the "
  "defective runs alongside the corrected analysis, as the field study did: a claim that a "
  "defect ‘would have changed the result’ is itself a computational claim, and it "
  "deserves the same verifiability as the result." % (N_DISC, N_CASOS))

h2("5.2. Reproducibility, replicability and validity")
P("None of this competes with the reproducibility agenda; it completes it. Marwick's (2017) "
  "programme makes an analysis repeatable by others, and that is the precondition for everything "
  "here —a benchmark of the kind this paper publishes is only auditable because it ships as "
  "runnable code, and the two production engines could only be measured because they are open "
  "source (Ducke, 2012). But the two guarantees must not be confused. Reproducibility certifies "
  "the transport of a computation; validation certifies its content. The field episode behind "
  "this paper was fully reproducible at every moment during which it was wrong.")
P("The taxonomy of Kedron et al. (2021) makes the point precise. Reproducibility asks whether the "
  "same data and code return the same result; replicability asks whether new data return the same "
  "finding. A silent failure of the engine survives both, because the defective procedure travels "
  "with the study: a second team re-running the deposited code reproduces the inverted sign, and a "
  "second team applying the same shipped default to a new landscape replicates the same wrong "
  "verdicts. What the two guarantees leave uncovered is the correspondence between the procedure "
  "and the quantity it claims to compute, and that correspondence can only be established against "
  "cases where the answer is known independently of the procedure —which is what a benchmark with "
  "derived expectations provides, and what real terrain, by its nature, cannot. This is the "
  "oracle problem of Section 2.2 stated in the vocabulary of open science, and the answer is the "
  "same: the discipline's methodological literature should publish benchmarks alongside methods, "
  "so that a new engine, a new plug-in or a new default can be measured rather than trusted.")
P("There is a theoretical corollary for how methods are argued in archaeology. Much of the "
  "visibility literature reviewed in Section 2.1 responds to uncertainty by modelling it —fuzzy "
  "viewsheds, probabilistic visibility, network models that are robust to individual edges— and "
  "that response is right for the uncertainty that comes from the data. It is the wrong response "
  "for the uncertainty that comes from defects, because a defect is not a distribution to be "
  "propagated but a mistake to be found, and propagating it only lends it the authority of an "
  "error bar. The two kinds of uncertainty demand different instruments, and the discipline has so "
  "far built only the first.")

h2("5.3. Implications for visibility studies")
P("For the practising analyst the results reduce to a short list of things a visibility paper "
  "should report and currently rarely does. The engine and its version; whether curvature and "
  "refraction were applied and with what coefficient, since Section 4.5 shows that the answer "
  "differs between two tools reachable from the same menu; the observer and target heights, since "
  "a target height of zero is a defect that one of those tools ships with; the sampling region of "
  "the null model together with diagnostics D1 and D2; and the evidence that the engine passes a "
  "benchmark of known answers. Kormann and Lock (2014) showed that curvature and refraction change "
  "results at archaeological ranges; this paper shows that whether they are applied at all can "
  "depend on a flag the analyst never saw. The plug-in of Čučković (2016) and the network methods "
  "of Brughmans et al. (2015) are only as sound as the lines of sight beneath them, and the "
  "benchmark deposited here can be run against either in minutes.")
P("The results also bear on how the field's null models are designed. Lake and Woodman (2003) and "
  "Wheatley and Gillings (2000) settled which comparison a visibility study should make; the "
  "laboratory shows that even the right comparison fails silently if the null is allowed to sample "
  "where no site could stand, or is denied orientations that the real configuration could have "
  "taken. Both are properties of the sampler, not of the null model as a concept, and both are "
  "checkable before any line of sight is computed.")

h2("5.4. Limitations")
P("The benchmark validates one algorithmic family: Boolean line-of-sight over a sampled profile "
  "with the effective-radius correction. Probabilistic and fuzzy viewsheds, and implementations "
  "with sub-cell interpolation, need their own cases, though the properties —reciprocity and "
  "the three monotonicities— transfer unchanged. The laboratory's landscapes are stylised; "
  "they are built to make the defects' mechanisms measurable, not to imitate any particular "
  "geography. The defect list is not a census: it contains every defect documented in the field "
  "episode plus plausible defaults, and the mutation methodology is the instrument by which the "
  "list is meant to grow. The two production engines were measured at one version each, and "
  "defaults change between releases; the benchmark is deposited precisely so that the measurement "
  "can be repeated. Finally, the laboratory's exactness holds for its own constructed "
  "scenarios; the p-value of a real study does not inherit it, because real sites are not placed "
  "by the null's rules. What transfers to the field is the measured behaviour of procedures, not "
  "of sites.")

h2("5.5. Future work")
P("The natural extension is horizontal: the same defect-injection methodology applies wherever "
  "archaeology computes on rasters —least-cost paths, hydrological modelling, predictive "
  "modelling— and each domain has its own silent defaults awaiting a benchmark. A second "
  "extension is comparative: Section 4.5 measured two engines at two configurations, and the same "
  "harness can be pointed at every published viewshed implementation, turning Fisher's (1993) "
  "observation of inter-implementation disagreement into a standing, attributable measurement "
  "that is updated with each release.")

# ================================================================= conclusions
h1("6. Conclusions")
P("A reproducible analysis reproduces its errors. This paper has shown, for archaeological "
  "visibility analysis, that a class of defects exists which no current control catches: they "
  "raise no error, return plausible output, survive review and re-execution, and decide the "
  "conclusion of the study that contains them. Three were documented in the field; seven are "
  "reproduced here. Against them the paper offers a benchmark whose expectations are derived and "
  "whose adequacy is measured, a laboratory in which the truth is known by construction, two "
  "diagnostics that cost nothing, and the finding that two of the engines archaeologists use every "
  "day are correct when configured and contradictory when not. The practices that follow are cheap "
  "and the code that implements them is deposited. What they add to the reproducibility programme "
  "is the one guarantee that programme cannot give: that what is being reproduced is right.")

# ================================================= statements and declarations
h1("Statements and Declarations")
etiqueta("Funding", after=3)
P("The author received no financial support for the research, authorship or publication of this "
  "article.", after=8)

etiqueta("Competing interests", after=3)
P("The author has no competing interests to declare that are relevant to the content of this "
  "article.", after=8)

etiqueta("Data and code availability", after=3)
P("The engine with switchable defects, the benchmark, the mutation harness, the landscape "
  "laboratory, the scripts that drive gdal_viewshed and r.viewshed, every result file and the "
  "scripts that generate the figures and this manuscript are openly deposited under an MIT licence "
  "at https://doi.org/%s (concept identifier, resolving to the latest version). The field study "
  "whose defects are reproduced here is likewise openly deposited, including its pre-correction "
  "runs, at https://doi.org/%s." % (DOI_ESTE, DOI_CASO), after=8)

etiqueta("Author contributions", after=3)
P("%s: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, "
  "Data curation, Writing – original draft, Writing – review and editing, Visualization."
  % AUTOR, after=10)

# ================================================================== references
etiqueta("References", after=6)
REFERENCES = [
    "Baker, M. (2016). 1,500 scientists lift the lid on reproducibility. Nature, 533(7604), "
    "452–454. https://doi.org/10.1038/533452a",
    "Brughmans, T., & Brandes, U. (2017). Visibility network patterns and methods for studying "
    "visual relational phenomena in archeology. Frontiers in Digital Humanities, 4, 17. "
    "https://doi.org/10.3389/fdigh.2017.00017",
    "Brughmans, T., Keay, S., & Earl, G. (2015). Understanding inter-settlement visibility in Iron "
    "Age and Roman southern Spain with exponential random graph models for visibility networks. "
    "Journal of Archaeological Method and Theory, 22(1), 58–143. "
    "https://doi.org/10.1007/s10816-014-9231-x",
    "Brunsdon, C. (2016). Quantitative methods I: Reproducible research and quantitative geography. "
    "Progress in Human Geography, 40(5), 687–696. https://doi.org/10.1177/0309132515599625",
    "Chen, T. Y., Kuo, F.-C., Liu, H., Poon, P.-L., Towey, D., Tse, T. H., & Zhou, Z. Q. (2018). "
    "Metamorphic testing: A review of challenges and opportunities. ACM Computing Surveys, 51(1), "
    "Article 4. https://doi.org/10.1145/3143561",
    "Claessen, K., & Hughes, J. (2000). QuickCheck: A lightweight tool for random testing of Haskell "
    "programs. In Proceedings of the Fifth ACM SIGPLAN International Conference on Functional "
    "Programming (pp. 268–279). ACM. https://doi.org/10.1145/351240.351266",
    "Čučković, Z. (2016). Advanced viewshed analysis: A Quantum GIS plug-in for the analysis of "
    "visual landscapes. The Journal of Open Source Software, 1(4), 32. "
    "https://doi.org/10.21105/joss.00032",
    "DeMillo, R. A., Lipton, R. J., & Sayward, F. G. (1978). Hints on test data selection: Help for "
    "the practicing programmer. Computer, 11(4), 34–41. https://doi.org/10.1109/C-M.1978.218136",
    "Ducke, B. (2012). Natives of a connected world: Free and open source software in archaeology. "
    "World Archaeology, 44(4), 571–579. https://doi.org/10.1080/00438243.2012.743259",
    "Fisher, P. F. (1993). Algorithm and implementation uncertainty in viewshed analysis. "
    "International Journal of Geographical Information Systems, 7(4), 331–347. "
    "https://doi.org/10.1080/02693799308901965",
    "Gillings, M. (2015). Mapping invisibility: GIS approaches to the analysis of hiding and "
    "seclusion. Journal of Archaeological Science, 62, 1–14. "
    "https://doi.org/10.1016/j.jas.2015.06.015",
    "Gillings, M. (2017). Mapping liminality: Critical frameworks for the GIS-based modelling of "
    "visibility. Journal of Archaeological Science, 84, 121–128. "
    "https://doi.org/10.1016/j.jas.2017.05.004",
    "Hatton, L. (1997). The T experiments: Errors in scientific software. IEEE Computational "
    "Science and Engineering, 4(2), 27–38. https://doi.org/10.1109/99.609829",
    "Hatton, L., & Roberts, A. (1994). How accurate is scientific software? IEEE Transactions on "
    "Software Engineering, 20(10), 785–797. https://doi.org/10.1109/32.328993",
    "Herndon, T., Ash, M., & Pollin, R. (2014). Does high public debt consistently stifle economic "
    "growth? A critique of Reinhart and Rogoff. Cambridge Journal of Economics, 38(2), 257–279. "
    "https://doi.org/10.1093/cje/bet075",
    "Ivie, P., & Thain, D. (2018). Reproducibility in scientific computing. ACM Computing Surveys, "
    "51(3), Article 63. https://doi.org/10.1145/3186266",
    "Jia, Y., & Harman, M. (2011). An analysis and survey of the development of mutation testing. "
    "IEEE Transactions on Software Engineering, 37(5), 649–678. "
    "https://doi.org/10.1109/TSE.2010.62",
    "Kanewala, U., & Bieman, J. M. (2014). Testing scientific software: A systematic literature "
    "review. Information and Software Technology, 56(10), 1219–1232. "
    "https://doi.org/10.1016/j.infsof.2014.05.006",
    "Kedron, P., Li, W., Fotheringham, S., & Goodchild, M. (2021). Reproducibility and "
    "replicability: Opportunities and challenges for geospatial research. International Journal "
    "of Geographical Information Science, 35(3), 427–445. "
    "https://doi.org/10.1080/13658816.2020.1802032",
    "Kormann, M., & Lock, G. (2014). Exploring the effects of curvature and refraction on "
    "GIS-based visibility studies. In G. Earl, T. Sly, A. Chrysanthi, P. Murrieta-Flores, C. "
    "Papadopoulos, I. Romanowska, & D. Wheatley (Eds.), Archaeology in the digital era: Papers "
    "from the 40th Annual Conference of Computer Applications and Quantitative Methods in "
    "Archaeology (CAA), Southampton, 26–29 March 2012 (pp. 428–437). Amsterdam University Press. "
    "https://doi.org/10.1515/9789048519590-046",
    "Lake, M. W., & Woodman, P. E. (2003). Visibility studies in archaeology: A review and case "
    "study. Environment and Planning B: Planning and Design, 30(5), 689–707. "
    "https://doi.org/10.1068/b29122",
    "Lake, M. W., Woodman, P. E., & Mithen, S. J. (1998). Tailoring GIS software for "
    "archaeological applications: An example concerning viewshed analysis. Journal of "
    "Archaeological Science, 25(1), 27–38. https://doi.org/10.1006/jasc.1997.0197",
    "Mamani Calisaya, M. V., Mamani Calisaya, D. N., Alanoca Arocutipa, V., & Alanoca Laura, S. L. "
    "(2026). Intervisibilidad de sitios arqueológicos en la cuenca del Titicaca: Código, datos "
    "derivados y contraejemplos (Version 1.1.0) [Data set and software]. Zenodo. "
    "https://doi.org/10.5281/zenodo.22176260",
    "Marwick, B. (2017). Computational reproducibility in archaeological research: Basic principles "
    "and a case study of their implementation. Journal of Archaeological Method and Theory, 24(2), "
    "424–450. https://doi.org/10.1007/s10816-015-9272-9",
    "Merali, Z. (2010). Computational science: ...Error. Nature, 467(7317), 775–777. "
    "https://doi.org/10.1038/467775a",
    "Miller, G. (2006). A scientist's nightmare: Software problem leads to five retractions. "
    "Science, 314(5807), 1856–1857. https://doi.org/10.1126/science.314.5807.1856",
    "Nackaerts, K., Govers, G., & Van Orshoven, J. (1999). Accuracy assessment of probabilistic "
    "visibilities. International Journal of Geographical Information Science, 13(7), 709–721. "
    "https://doi.org/10.1080/136588199241076",
    "Nüst, D., & Pebesma, E. (2021). Practical reproducibility in geography and geosciences. "
    "Annals of the American Association of Geographers, 111(5), 1300–1310. "
    "https://doi.org/10.1080/24694452.2020.1806028",
    "Peng, R. D. (2011). Reproducible research in computational science. Science, 334(6060), "
    "1226–1227. https://doi.org/10.1126/science.1213847",
    "Riggs, P. D., & Dean, D. J. (2007). An investigation into the causes of errors and "
    "inconsistencies in predicted viewsheds. Transactions in GIS, 11(2), 175–196. "
    "https://doi.org/10.1111/j.1467-9671.2007.01040.x",
    "Sandve, G. K., Nekrutenko, A., Taylor, J., & Hovig, E. (2013). Ten simple rules for "
    "reproducible computational research. PLoS Computational Biology, 9(10), e1003285. "
    "https://doi.org/10.1371/journal.pcbi.1003285",
    "Schmidt, S. C., & Marwick, B. (2020). Tool-driven revolutions in archaeological science. "
    "Journal of Computer Applications in Archaeology, 3(1), 18–32. https://doi.org/10.5334/jcaa.29",
    "Segura, S., Fraser, G., Sanchez, A. B., & Ruiz-Cortés, A. (2016). A survey on metamorphic "
    "testing. IEEE Transactions on Software Engineering, 42(9), 805–824. "
    "https://doi.org/10.1109/TSE.2016.2532875",
    "Soergel, D. A. W. (2015). Rampant software errors may undermine scientific results. "
    "F1000Research, 3, 303. https://doi.org/10.12688/f1000research.5930.2",
    "Stodden, V., Seiler, J., & Ma, Z. (2018). An empirical analysis of journal policy "
    "effectiveness for computational reproducibility. Proceedings of the National Academy of "
    "Sciences, 115(11), 2584–2589. https://doi.org/10.1073/pnas.1708290115",
    "Wheatley, D., & Gillings, M. (2000). Vision, perception and GIS: Developing enriched "
    "approaches to the study of archaeological visibility. In G. R. Lock (Ed.), Beyond the map: "
    "Archaeology and spatial technologies (pp. 1–27). IOS Press.",
]
for ref in REFERENCES:
    p = P(ref, 9, after=4)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.6)

# --------------------------------------------------------------------- salida
doc.save(OUT)
docmeta.limpiar(OUT, autor="", asunto="",
                titulo=doc.paragraphs[0].text + ": " + doc.paragraphs[1].text)

palabras = sum(len(p.text.split()) for p in doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            palabras += len(c.text.split())
ps_ = [p.text.strip() for p in doc.paragraphs]
i_ini = next(i for i, t in enumerate(ps_) if t.startswith("1. Introduction"))
i_dec = ps_.index("Statements and Declarations")
cuerpo = sum(len(t.split()) for t in ps_[i_ini:i_dec])
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            cuerpo += len(c.text.split())
print("Manuscrito ->", OUT)
print("metadatos con contenido:", docmeta.informe(OUT) or "ninguno")
print("palabras: %d en total | %d en el cuerpo (Introduction a Declarations) | resumen: %d | "
      "figuras: %d | tablas: %d | referencias: %d"
      % (palabras, cuerpo, len(ABSTRACT.split()), len(doc.inline_shapes), len(doc.tables),
         len(REFERENCES)))
