# -*- coding: utf-8 -*-
"""
Genera el manuscrito en ingles, leyendo cada cifra de los JSON de resultados.

La disciplina es la del caso de estudio que este articulo describe: ningun
numero se escribe a mano. Los que proceden de un calculo se leen de
benchmark.json y calibracion.json; los estructurales (la distancia critica de
curvatura) se derivan aqui de las mismas constantes que usa el motor.

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

DOI_CASO = "10.5281/zenodo.22176260"
DOI_ESTE_TXT = DOI_ESTE if "DOI_ESTE" in dir() else None
AUTOR = "Milton Vladimir Mamani Calisaya"
FILIACION = "Universidad Nacional del Altiplano, Puno, Perú"
CORREO = "mmamanic@unap.edu.pe"
ORCID_A = "0000-0002-0676-0989"
DOI_ESTE = "10.5281/zenodo.22242923"


def f(x, dec=2):
    return ("%%.%df" % dec) % x


def fz(x):
    """z con signo explicito, que es como se leen los contrastes."""
    return "%+.2f" % x


def pct(x, dec=0):
    return ("%%.%df" % dec) % (100.0 * x)


# ------------------------------------------------------------------ documento
# El lenguaje visual es el de una maqueta editorial sobria: una sola familia
# (Arial, que la revista pide «commonly available»), jerarquia por tamano,
# versalitas e interletrado en los titulos, reglas finas en el gris calido de
# las figuras, tablas sin bordes verticales al modo booktabs, folio y cabecera.
# Nada decorativo: todo lo que se ve ordena la lectura.
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
    """Espaciado entre letras, en veintavos de punto: el detalle de versalitas."""
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
    """lados: dict lado -> grosor en octavos de punto; el resto queda sin borde."""
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
    # versalitas con interletrado: la marca tipografica del documento
    return P(t, 11.5, True, align=WD_ALIGN_PARAGRAPH.LEFT, before=16, after=6,
             caps=True, track=16)


def h2(t):
    return P(t, 10.5, True, align=WD_ALIGN_PARAGRAPH.LEFT, before=10, after=4,
             color=TINTA_SUAVE)


def etiqueta(t, after=3):
    """Rotulos de bloque —Abstract, Keywords, References— en versalitas."""
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
    """Numero de pagina como campo de Word, no como texto fijo."""
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
    r = run(ph, "Silent failures in archaeological visibility analysis", 8,
            color=GRIS_PIE, caps=True, track=12)
    pf = sec.footer.paragraphs[0]
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _campo_pagina(pf)


cabecera_y_folio()

# numeracion continua de lineas: lo que un revisor de Elsevier espera encontrar
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

# bloque de autoria: revision de anonimo simple, sin portada separada
P(AUTOR, 11, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
P(FILIACION, 9.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, color=TINTA_SUAVE)
P("Corresponding author: %s  ·  ORCID %s" % (CORREO, ORCID_A),
  9, align=WD_ALIGN_PARAGRAPH.CENTER, after=16, color=TINTA_SUAVE)

etiqueta("Abstract")
P("Computational reproducibility guarantees that an analysis can be re-run and will return the same "
  "result. It does not guarantee that the result is true: a reproducible pipeline reproduces its "
  "errors faithfully. This paper characterises a class of defects in archaeological "
  "visibility analysis that crash nothing, produce plausible and interpretable output, survive both "
  "peer review and re-execution, and invert or erase the conclusion of the study that contains them. "
  "Three members of the class were documented in a recent Titicaca-basin intervisibility study and "
  "are reproduced here under controlled conditions. Two instruments are presented. "
  "First, an executable benchmark for line-of-sight engines —%d terrain cases with derived "
  "expectations plus %d behavioural properties— whose own adequacy is measured by mutation "
  "analysis: every consequential defect is detected, and one is proven behaviourally equivalent to "
  "the correct engine. "
  "Second, a synthetic-landscape laboratory where the truth is known by construction, so that "
  "defective designs are measured against exact expectations. "
  "Sampling null placements over water destroys statistical "
  "power (%s %% against a theoretical ceiling of %s %%); a tightly cropped sampling region biases "
  "the contrast in a direction set by the alignment between site configuration and terrain grain "
  "(Spearman rho = %s) —invisible to a marginal calibration audit— and halves power under a "
  "real effect. Two cheap "
  "diagnostics flag both defects without requiring ground truth. Five hand-written expectations in "
  "this research failed for the very cause the benchmark targets: derive "
  "expectations, do not write them by hand, and "
  "audit the tests with the same rigour as the code."
  % (N_CASOS, N_PROPS, pct(RESU["S1"]["agua"]["rechazo"]), pct(POT_TEO),
     f(MEC["spearman_desalineacion"], 2)),
  after=8, size=9.5)
_borde_parrafo(doc.paragraphs[-1], "left")
doc.paragraphs[-1].paragraph_format.left_indent = Cm(0.35)

etiqueta("Keywords")
P("viewshed analysis; software validation; mutation testing; reproducibility; null models; "
  "geographic information systems", after=18, size=9.5, italic=True, color=TINTA_SUAVE)

# ================================================================ introduction
h1("1. Introduction")

P("Archaeology has spent a decade building the case for computational reproducibility. The argument "
  "is settled: analyses should ship their code and data, be version-controlled, and re-run from top "
  "to bottom on demand (Marwick 2016; Peng 2011; Sandve et al. 2013). This paper is about what "
  "that programme, on its own, cannot deliver. Re-running an analysis verifies that the code "
  "produces the reported numbers; it says nothing about whether the numbers are right. A pipeline "
  "with an inverted sign is perfectly reproducible. It reproduces the inverted sign.")

P("The distinction is not hypothetical. A sign error in a data-processing script forced the "
  "retraction of five protein-structure papers, three of them in Science (Miller 2006). A "
  "spreadsheet error silently shaped a decade of austerity policy before anyone re-derived the "
  "numbers (Herndon, Ash & Pollin 2013). Software faults of this kind are common enough that "
  "Soergel (2015) argued they may undermine results across computational science generally. What "
  "makes these cases instructive is not that software failed but how it failed: no crash, no "
  "warning, output of entirely plausible appearance.")

P("Archaeological visibility analysis —a methodological tradition reviewed by Lake and Woodman "
  "(2003)— is unusually exposed to this failure mode. A viewshed or intervisibility computation "
  "returns maps and networks that look reasonable under almost any defect, and there is no ground "
  "truth on real terrain against which to notice that they are wrong; Fisher (1993) showed three "
  "decades ago that independent implementations of the same viewshed disagree substantially "
  "without any of them being obviously broken. Reviewers see "
  "results, not code, so review does not catch the defect. Reproduction re-executes the same code, "
  "so reproduction does not catch it either. The defect passes through every control the discipline "
  "currently operates.")

P("A recent intervisibility study of 180 archaeological sites in the Titicaca basin documented "
  "three such defects encountered —and corrected— during its own analysis (Mamani Calisaya, "
  "Mamani Calisaya & Alanoca Arocutipa 2026). The sign of the Earth-curvature correction was "
  "inverted, which renders the Earth concave and lets no relief block any long-range view. The "
  "elevation model assigned a constant elevation to the lake, a perfect plane covering 30.6 %% of "
  "the study area that blocks nothing and inflated the null model until a real effect vanished "
  "(z = %s against z = %s once masked). And a tightly fitted raster crop admitted only 244 "
  "of 360 orientations of the rigid null model, inflating the contrast from z = %s to z = %s. "
  "None of the three produced any visible failure. Each was found by accident or by a purpose-built "
  "check, not by inspection of results."
  % (fz(Z_CAMPO_AGUA), fz(Z_CAMPO_OK), fz(Z_CAMPO_OK), fz(Z_CAMPO_RECORTE)))

P("This paper treats that episode as a specimen and builds the instruments the discipline lacks. "
  "Its contributions are: (1) a characterisation of the silent failure class and a two-level "
  "taxonomy —defects of the geometric engine versus defects of the analysis design— with seven "
  "concrete, field-documented or field-plausible members; (2) an executable benchmark for "
  "line-of-sight engines whose adequacy is itself measured, by mutation analysis, rather than "
  "asserted; (3) a synthetic-landscape laboratory in which the truth is known by construction, so "
  "the damage each design defect does to statistical inference is measured exactly; and (4) two "
  "diagnostics and a five-point protocol that detect the documented defects at negligible cost, "
  "before any real terrain is touched.")

# ============================================================ the failure class
h1("2. The failure class")

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
  "default that mainstream software makes easy; both design defects are documented.")

table("Table 1.", "The seven defects studied. The first five are injected into the line-of-sight "
      "engine; the last two into the design of the null-model contrast. ‘Documented’ "
      "means observed and quantified in the Titicaca field study.",
      ["Defect", "Level", "Mechanism", "Status"],
      [["Curvature subtracted", "engine", "Earth rendered concave; nothing blocks at range", "documented"],
       ["Curvature omitted", "engine", "defensible below a few km, wrong beyond", "plausible default"],
       ["Target height zero", "engine", "monument treated as a point on the ground", "plausible default"],
       ["Endpoints included", "engine", "observer blocks itself on its own relief", "equivalent (see 4.1)"],
       ["Coarse profile sampling", "engine", "narrow barriers fall between samples", "plausible shortcut"],
       ["Water left unmasked", "design", "a flat lake that blocks nothing feeds the null", "documented"],
       ["Tightly cropped region", "design", "null placements lose orientations that do not fit", "documented"]])

# ==================================================================== methods
h1("3. Materials and methods")
P("Figure 1 gives the architecture. Two instruments answer two different questions —whether the "
  "geometry is right, and whether the inference is right— and converge on one rule: only a "
  "validated engine and a diagnosed design touch real terrain.")
figure("fig_pipeline.png", "Figure 1.",
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
  "derived value. The reason for this discipline appears in Section 5.2." % (N_CASOS, f(D_CRIT_KM, 1)))
P("The second part is %d behavioural properties checked over hundreds of random rugged terrains: "
  "visibility is reciprocal; raising the observer never removes visibility; over a plane, "
  "visibility lost to curvature never returns with further distance; raising a barrier never "
  "unblocks a view. These are metamorphic relations in the sense of the software-testing "
  "literature (Segura, Fraser & Sanchez 2016), and their value is that a defective engine "
  "cannot satisfy them by coincidence, because there is no specific case to be accidentally "
  "right about (Claessen & Hughes 2000)." % N_PROPS)

h2("3.3. Mutation analysis: measuring the benchmark itself")
P("A validation suite that passes the correct engine proves little; the question is whether it "
  "would fail a defective one. Mutation analysis answers exactly this (DeMillo, Lipton & Sayward "
  "1978; Jia & Harman 2011): each defect of Section 3.1 is switched on in turn and the full "
  "benchmark is run against the mutated engine. A defect that no test detects marks a hole in the "
  "benchmark —unless the mutation does not alter observable behaviour at all, in which case it "
  "is an equivalent mutant and detecting it is impossible in principle. The two situations are "
  "distinguished empirically, by sweeping the mutant against the reference engine over thousands "
  "of random terrain pairs and endpoint configurations.")

h2("3.4. A landscape laboratory with ground truth by construction")
P("Engine defects can be caught by geometry. Design defects cannot: they operate above a correct "
  "engine, and on real terrain there is no way to know what the contrast should have concluded. "
  "The laboratory therefore manufactures landscapes where the truth is known exactly. Each "
  "replicate generates an anisotropic synthetic terrain —ridges with a dominant, randomised "
  "grain direction— with a lake occupying about a quarter of the map, built the way real "
  "elevation models build lakes: by flooding a basin to a constant elevation (Figure 3a). An elongated cloud "
  "of %d sites is then placed under two scenarios. In scenario S0 the cloud is placed by the very "
  "rules the rigid null model uses to place its own draws; observed and null placements are then "
  "exchangeable, and the p-value of a correct contrast is uniform by symmetry —exactly, up to "
  "ties in the discrete density, which can only make the test conservative. Every measured "
  "departure from uniformity is therefore attributable to the procedure, not to chance. In scenario S1 the cloud is placed at the best of %d random "
  "placements, which makes ‘sited where it sees more than the same configuration would "
  "elsewhere’ true by construction; the theoretical power of a correct contrast follows from "
  "rank symmetry and is computed alongside the experiment." % (32, CFG["k_mejor"]))
P("Each replicate then runs the same contrast three times on identical data: with the correct "
  "design, with null placements allowed onto the water, and with the null sampling region cropped "
  "to the bounding box of the observed cloud plus %d cells. The design is paired: any difference "
  "between procedures is attributable to the defect alone. %d replicates were run, each with %d "
  "null placements per contrast." % (CFG["margen_ajustado_celdas"], R_, CFG["n_null"]))

h2("3.5. Diagnostics")
P("Two checks are computed in every run, neither requiring ground truth. D1: the fraction of "
  "accepted null placements with at least one site on water —in a sound design, identically "
  "zero. D2: the fraction of the 360 placement orientations that fit geometrically inside the "
  "sampling region (Figure 3b–c) —in a sound design, 100 %. Both are near-free to compute, and either would "
  "have flagged its corresponding field defect before a single line of sight was calculated.")

# ==================================================================== results
h1("4. Results")

h2("4.1. The benchmark and its mutation matrix")
P("The reference engine passes all %d tests. Table 2 gives the mutation matrix. Every defect with "
  "observable consequences is detected, most by several independent tests. The exception is "
  "instructive: including the endpoint cells in the blocking test —a plausible off-by-one — "
  "turns out to be behaviourally equivalent to the correct engine, because the sight line is "
  "anchored at terrain-plus-height on both endpoints and by construction can never be exceeded "
  "there. The sweep of Section 3.3 found no difference in any of %s paired evaluations. "
  "Reporting this matters: mutation analysis without an equivalence check would count it as a "
  "hole in the benchmark, making the suite look weaker than it is (Jia & Harman 2011). "
  "Figure 2 dissects two of the killed mutants on single terrain profiles: in each panel the "
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

figure("fig_anatomia.png", "Figure 2.",
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
P("Table 3 and Figure 4 give the laboratory results. The correct procedure behaves exactly as "
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
  "observed cloud and the terrain grain (Spearman rho = %s, p = %s; Figure 4c). Clouds lying "
  "along the grain see their contrast inflated, clouds lying across it deflated, and the effects "
  "cancel only across an ensemble of landscapes that no analyst ever has —any single study "
  "sits at one point of Figure 4c and inherits that point's bias. The field case is consistent "
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

figure("fig_laboratorio.png", "Figure 3.",
       "The landscape laboratory. (a) One synthetic replicate: anisotropic terrain with a lake "
       "built by flooding a basin to a constant elevation, the observed elongated cloud (red), "
       "three null placements (grey), and the tightly cropped sampling region (dashed). "
       "(b) Diagnostic D2 on the full region: all 360 orientations of the null placement fit. "
       "(c) The same diagnostic on the cropped region: only orientations near the cloud's own "
       "axis survive. The field-study analogue of this check would have read 244/360.")

figure("fig_consecuencias.png", "Figure 4.",
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

# ================================================================== discussion
h1("5. Discussion")

P("The instruments presented here are cheap, and the failures they target are not hypothetical: "
  "all three field-documented defects pass silently through review and reproduction, and two of "
  "them singlehandedly decide the conclusion of a study. Five practices follow from the results, "
  "in rising order of novelty for the discipline.")
P("First, validate the geometric engine against synthetic terrains of known answer before it "
  "touches real terrain; on real terrain there is nothing to validate against (Fisher 1993). "
  "Second, derive test expectations from theory wherever a closed form exists; Section 4.2 shows "
  "hand-written expectations failing at a rate —five of five errors traceable to one forgotten "
  "term— that no one would tolerate in the code under test. Third, audit the validation suite "
  "itself by mutation analysis, distinguishing equivalent mutants from holes; it is the only "
  "instrument here that caught a test passing for the wrong reason. Fourth, diagnose the null "
  "model's sampler directly: placement validity (D1) and orientation coverage (D2) would have "
  "caught both design defects at the cost of two printed numbers. Fifth, publish the defective "
  "runs alongside the corrected analysis, as the field study did: a claim that a defect ‘would "
  "have changed the result’ is itself a computational claim, and it deserves the same "
  "verifiability as the result.")
P("None of this competes with the reproducibility agenda; it completes it. Marwick's (2016) "
  "programme makes an analysis repeatable by others, and that is the precondition for everything "
  "here —a benchmark of the kind this paper publishes is only auditable because it ships as "
  "runnable code. But the two guarantees must not be confused. Reproducibility certifies the "
  "transport of a computation; validation certifies its content. The field episode behind this "
  "paper was fully reproducible at every moment during which it was wrong.")

h2("5.1. Limitations")
P("The benchmark validates one algorithmic family: Boolean line-of-sight over a sampled profile "
  "with the effective-radius correction. Probabilistic and fuzzy viewsheds, and implementations "
  "with sub-cell interpolation, need their own cases, though the properties —reciprocity and "
  "the three monotonicities— transfer unchanged. The laboratory's landscapes are stylised; "
  "they are built to make the defects' mechanisms measurable, not to imitate any particular "
  "geography. The defect list is not a census: it contains every defect documented in the field "
  "episode plus plausible defaults, and the mutation methodology is the instrument by which the "
  "list is meant to grow. Finally, the laboratory's exactness holds for its own constructed "
  "scenarios; the p-value of a real study does not inherit it, because real sites are not placed "
  "by the null's rules. What transfers to the field is the measured behaviour of procedures, not "
  "of sites.")

h2("5.2. Future work")
P("The natural extension is horizontal: the same defect-injection methodology applies wherever "
  "archaeology computes on rasters —least-cost paths, hydrological modelling, predictive "
  "modelling— and each domain has its own silent defaults awaiting a benchmark. A second "
  "extension is comparative: running published viewshed implementations against this suite would "
  "turn Fisher's (1993) observation of inter-implementation disagreement into a measurable, "
  "attributable quantity.")

# ======================================================== data availability
h1("6. Data and code availability")
P("The engine with switchable defects, the benchmark, the mutation harness, the landscape "
  "laboratory, every result file and the scripts that generate the figures and this manuscript "
  "are openly deposited. The software depends only on NumPy (and Matplotlib for figures). The "
  "field study whose defects are reproduced here is likewise openly deposited, including its "
  "pre-correction runs (doi:%s). The present deposit is at doi:%s "
  "(concept identifier, resolving to the latest version)." % (DOI_CASO, DOI_ESTE))

# ================================================================== references
etiqueta("Funding", after=3)
P("This research received no specific grant from any funding agency in the public, commercial, "
  "or not-for-profit sectors.", after=8)

etiqueta("CRediT authorship contribution statement", after=3)
P("%s: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, "
  "Data curation, Writing – original draft, Writing – review & editing, Visualization."
  % AUTOR, after=8)

etiqueta("Declaration of competing interests", after=3)
P("The author declares no competing financial interests or personal relationships that could "
  "have appeared to influence the work reported in this paper.", after=8)

etiqueta("Declaration of generative AI in the manuscript preparation process", after=3)
P("During the preparation of this work the author used Claude (Anthropic) to assist in developing "
  "and testing the analysis code, drafting the manuscript, and generating the figures. The author "
  "reviewed, verified and edited all output —including through the automated audits deposited with "
  "the code— and takes full responsibility for the content of this article.", after=10)

etiqueta("References", after=6)
for ref in [
    "Claessen, K and Hughes, J 2000 QuickCheck: a lightweight tool for random testing of Haskell "
    "programs. In: Proceedings of the Fifth ACM SIGPLAN International Conference on Functional "
    "Programming, 268–279. DOI: https://doi.org/10.1145/351240.351266",
    "DeMillo, R A, Lipton, R J and Sayward, F G 1978 Hints on test data selection: help for the "
    "practicing programmer. Computer, 11(4): 34–41. DOI: https://doi.org/10.1109/C-M.1978.218136",
    "Fisher, P F 1993 Algorithm and implementation uncertainty in viewshed analysis. International "
    "Journal of Geographical Information Systems, 7(4): 331–347. "
    "DOI: https://doi.org/10.1080/02693799308901965",
    "Herndon, T, Ash, M and Pollin, R 2013 Does high public debt consistently stifle economic "
    "growth? A critique of Reinhart and Rogoff. Cambridge Journal of Economics, 38(2): 257–279. "
    "DOI: https://doi.org/10.1093/cje/bet075",
    "Jia, Y and Harman, M 2011 An analysis and survey of the development of mutation testing. IEEE "
    "Transactions on Software Engineering, 37(5): 649–678. DOI: https://doi.org/10.1109/TSE.2010.62",
    "Lake, M W and Woodman, P E 2003 Visibility studies in archaeology: a review and case study. "
    "Environment and Planning B: Planning and Design, 30(5): 689–707. "
    "DOI: https://doi.org/10.1068/b29122",
    "Mamani Calisaya, M V, Mamani Calisaya, D N and Alanoca Arocutipa, V 2026 Intervisibilidad de "
    "sitios arqueológicos en la cuenca del Titicaca: código, datos derivados y contraejemplos "
    "[data set and software]. Zenodo. DOI: https://doi.org/10.5281/zenodo.22176260",
    "Marwick, B 2016 Computational reproducibility in archaeological research: basic principles "
    "and a case study of their implementation. Journal of Archaeological Method and Theory, 24(2): "
    "424–450. DOI: https://doi.org/10.1007/s10816-015-9272-9",
    "Miller, G 2006 A scientist's nightmare: software problem leads to five retractions. Science, "
    "314(5807): 1856–1857. DOI: https://doi.org/10.1126/science.314.5807.1856",
    "Peng, R D 2011 Reproducible research in computational science. Science, 334(6060): "
    "1226–1227. DOI: https://doi.org/10.1126/science.1213847",
    "Sandve, G K, Nekrutenko, A, Taylor, J and Hovig, E 2013 Ten simple rules for reproducible "
    "computational research. PLoS Computational Biology, 9(10): e1003285. "
    "DOI: https://doi.org/10.1371/journal.pcbi.1003285",
    "Segura, S, Fraser, G, Sanchez, A B and Ruiz-Cortés, A 2016 A survey on metamorphic testing. "
    "IEEE Transactions on Software Engineering, 42(9): 805–824. "
    "DOI: https://doi.org/10.1109/TSE.2016.2532875",
    "Soergel, D A W 2015 Rampant software errors may undermine scientific results. F1000Research, "
    "3: 303. DOI: https://doi.org/10.12688/f1000research.5930.2",
]:
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
print("Manuscrito ->", OUT)
print("metadatos con contenido:", docmeta.informe(OUT) or "ninguno")
print("palabras: %d | figuras: %d | tablas: %d" % (palabras, len(doc.inline_shapes), len(doc.tables)))
