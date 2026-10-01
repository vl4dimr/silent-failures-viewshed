# -*- coding: utf-8 -*-
"""
Genera el manuscrito en ingles, leyendo cada cifra de los JSON de resultados.

La disciplina es la del caso de estudio que este articulo describe: ninguna
cifra que proceda de un calculo se escribe a mano. Se leen de benchmark.json,
calibracion.json, comparacion_motores.json, figuras/meta.json y de los ficheros
del caso de campo copiados en data/caso_titicaca (con su README_origen.txt,
que registra la unica cifra del estudio de campo sin fichero de resultados:
las orientaciones que admitia su recorte, que el texto cita como cifra
declarada por ese estudio).

Version final para Journal of Archaeological Method and Theory (Springer,
anonimo simple, ingles britanico), 30/09/2026: banco corregido (el rasgo
decide), distancia critica exacta, propiedades nuevas y hallazgo de las
propiedades v1, motores invocados directamente con sus valores de fabrica
completos, estadistica declarada, justicia con el software, dos tablas nuevas
(casos y parametros a declarar), referencias con cursivas y politica
tipografica (sin rayas en el cuerpo, apostrofo y signo menos tipograficos).

Salida: manuscript_silent_failures.docx
"""
import json
import math
import re
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Mm, Pt, RGBColor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docmeta
from los_engine import K_REFRACTION, R_EARTH

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
FIG = os.path.join(RES, "figuras")
OUT = os.path.join(BASE, "manuscript_silent_failures.docx")


def _j(*ruta):
    return json.load(open(os.path.join(*ruta), encoding="utf-8"))


BEN = _j(RES, "benchmark.json")
CAL = _j(RES, "calibracion.json")
FMETA = _j(FIG, "meta.json")
MOT = _j(RES, "comparacion_motores.json")

# ------------------------------------------------------------ caso de campo
_CT = os.path.join(BASE, "data", "caso_titicaca")
_NR = _j(_CT, "nulo_rigido.json")                 # el contraste corregido
_NS = _j(_CT, "nulo_rigido_sin_mascara.json")     # el contraejemplo del agua
_NC = _j(_CT, "nulo_rigido_n300.json")            # el contraejemplo del recorte
Z_CAMPO_OK = _NR["por_alcance"]["5000"]["z"]
Z_CAMPO_AGUA = _NS["por_alcance"]["5000"]["z"]
Z_CAMPO_RECORTE = _NC["por_alcance"]["5000"]["z"]
# el raster sin mascara es el corregido: su fraccion de agua es la de nulo_rigido.json
AGUA_CAMPO = _NR["fraccion_agua"]
AGUA_RECORTE = _NC["fraccion_agua"]
N_SITIOS_CAMPO = _j(_CT, "nulos.json")["parametros"]["n_sitios"]
# Cifra declarada por el estudio de campo, sin fichero de resultados que la
# respalde: se lee del registro de procedencia y el texto la atribuye al estudio.
_ORIGEN = open(os.path.join(_CT, "README_origen.txt"), encoding="utf-8").read()
_m = re.search(r"«(\d+) de (\d+) orientaciones»", _ORIGEN)
ORIENT_CAMPO, ORIENT_TOTAL_CAMPO = int(_m.group(1)), int(_m.group(2))

# ------------------------------------------------------------------ banco
MC = BEN["motor_correcto"]
CASOS = MC["casos"]
N_CASOS = len(CASOS)
N_PROPS = len(MC["propiedades"])
N_TESTS = MC["pruebas"]
N_EVAL_PROPS = sum(p["comprobaciones"] for p in MC["propiedades"])
RASGO = MC["comprobacion_rasgo_decide"]
assert RASGO["ok"] and RASGO["casos_de_rasgo_en_que_decide"] == RASGO["casos_de_rasgo"]
CELDA = MC["celda_m"]
DCRIT = MC["distancia_critica"]
D_CRIT_KM = DCRIT["exacta_m"] / 1000.0
D_CRIT_V1_KM = DCRIT["aproximada_v1_m"] / 1000.0
MUT = BEN["mutantes"]
EQUIVALENTES = [d for d, v in MUT.items() if v.get("equivalente")]
NO_EQUIV = [d for d in MUT if d not in EQUIVALENTES]
PV1 = BEN["propiedades_v1"]
assert BEN["resumen"]["todo_mutante_no_equivalente_muere_por_caso_y_propiedad"]
_EQ = MUT[EQUIVALENTES[0]]
CONTRA = _EQ["contraejemplo_alturas_negativas"]
assert CONTRA["difieren"] and CONTRA["correcto"] and not CONTRA["mutante"]
# el resumen afirma que las propiedades v1 no detectaron ningun defecto
assert PV1["mutantes_detectados"] == 0


def caso(nombre):
    return next(c for c in CASOS if c["prueba"] == nombre)


# ------------------------------------------------------------ laboratorio
CFG = CAL["config"]
R_ = CFG["replicas"]
N_NULL = CFG["n_null"]
RESU = CAL["resumen"]
POT_TEO = RESU["potencia_teorica_S1_correcto"]
MEC = RESU["mecanismo_recorte"]
DIAG = RESU["diagnosticos"]
RUIDO_MC = 1.0 / math.sqrt(N_NULL)
assert MEC["dz_sd"] > 3 * RUIDO_MC
assert MEC["p_spearman"] < 0.001

# ---------------------------------------------------------------- motores
_G = MOT["motores"]["GDAL gdal_viewshed"]
_R = MOT["motores"]["GRASS r.viewshed"]
GD, RD = _G["defaults_documentados"], _R["defaults_documentados"]
DISC = MOT["discrepancia_entre_motores_de_fabrica"]
N_DISC = DISC["casos"]
N_COMPARTIDO = MOT["coincidencia_en_el_error_de_fabrica"]["casos"]
N_AMBOS_BIEN = MOT["ambos_aciertan_de_fabrica"]["casos"]
N_ACUERDO = N_CASOS - N_DISC
assert N_ACUERDO == N_COMPARTIDO + N_AMBOS_BIEN
G_TV = _G["direccion"]["declara_tapado_lo_visible"]
G_VT = _G["direccion"]["declara_visible_lo_tapado"]
R_TV = _R["direccion"]["declara_tapado_lo_visible"]
R_VT = _R["direccion"]["declara_visible_lo_tapado"]
assert G_VT == 0 and R_TV > 0 and R_VT > 0
# ambos motores envian el objetivo a ras de suelo
assert GD["tz"] == 0.0 and RD["target_elevation"] == 0.0
ATR_G, ATR_R = _G["atribucion"], _R["atribucion"]
assert ATR_G["tz"]["coinciden"] == N_CASOS
# los fallos de GRASS «ve lo tapado» son los planos lejanos, incluido el de 40 km
C40 = next(c for c in CASOS if c["prueba"].startswith("plano a 40 km"))
assert C40["prueba"] in _R["casos_que_falla_de_fabrica"]
# la discrepancia en que acierta GRASS: acierta solo porque sus dos defectos se compensan
_DET = {d["caso"]: d for d in MOT["detalle"]}
_ACIERTA_GRASS = [d["caso"] for d in DISC["detalle_direccion"] if d["acierta"] == "GRASS"]
COMPENSAN = all(not _DET[c]["atribucion_grass"]["curvatura_y_refraccion"]
                and caso(c)["terreno"] == "plano" and caso(c)["h_tgt"] > 0
                for c in _ACIERTA_GRASS)
assert COMPENSAN
assert all(caso(d["caso"])["terreno"] == "plano" for d in DISC["detalle_direccion"])
# comprobacion de la bandera -r de GRASS
_CR = _R["comprobacion_refraccion"]


def _umbral(modo):
    """Ultima distancia visible y primera tapada de una corrida sobre plano."""
    v = next(c["veredictos"] for c in _CR["corridas"] if c["modo"] == modo)
    ks = _CR["distancias_km"]
    ult = max((k for k in ks if v[k]), key=float)
    pri = min((k for k in ks if not v[k]), key=float)
    return ult, pri


REF_C = _umbral("-c")
REF_CSINR = _umbral("-c refraction_coeff=0.13 (sin -r; protocolo de la primera version)")
REF_CR = _umbral("-c -r refraction_coeff=0.13")
assert REF_C == REF_CSINR and REF_CR != REF_C and _CR["coef_sin_r_es_igual_que_c_solo"]
_DCP = _CR["distancia_critica_predicha_km"]
DIF_RADIO_M = abs(_DCP["-c -r 0.13 (R = a/(1-0.13))"] - _DCP["motor del articulo (R = 6371000/(1-0.13))"]) * 1000
A_ELIPSOIDE = int(re.search(r"a = (\d+) m", _R["elipsoide"]).group(1))

DOI_CASO = "10.5281/zenodo.22176260"
DOI_ESTE = "10.5281/zenodo.22242923"
AUTOR = "Milton Vladimir Mamani Calisaya"
FILIACION = "Universidad Nacional del Altiplano, Puno, Perú"
CORREO = "mmamanic@unap.edu.pe"
ORCID_A = "0000-0002-0676-0989"


# ------------------------------------------------------------ formato de cifras
def _menos(s):
    return s.replace("-", "−")


def f(x, dec=2):
    return _menos(("%%.%df" % dec) % x)


def fz(x):
    """z con signo explicito, que es como se leen los contrastes."""
    return _menos("%+.2f" % x)


def pct(x, dec=0):
    return _menos(("%%.%df" % dec) % (100.0 * x))


def g(x):
    return _menos("%g" % x)


def num(n):
    """Cero a nueve con letra; de diez en adelante, cifra (APA, Springer)."""
    return ("zero one two three four five six seven eight nine".split()[n]
            if 0 <= n <= 9 else str(n))


def Num(n):
    s = num(n)
    return s[0].upper() + s[1:]


def frac(a, b):
    return "%d/%d" % (a, b)


# ------------------------------------------------------------------ documento
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

TINTA = RGBColor(0x21, 0x1F, 0x1C)
TINTA_SUAVE = RGBColor(0x4A, 0x46, 0x3F)
GRIS_PIE = RGBColor(0x6E, 0x6A, 0x62)
REGLA = "55524B"
CREMA = "F2EFE9"

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


def _sin_numero(p):
    """Parrafos sin texto (reglas, imagenes, aire tras tablas) sin numero de linea."""
    p._p.get_or_add_pPr().append(OxmlElement("w:suppressLineNumbers"))
    return p


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
    # apostrofo tipografico en todo el documento: las comillas rectas de las
    # cadenas son posesivos o contracciones, nunca comillas de apertura
    r = p.add_run(t.replace("'", "’"))
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


def _con_siguiente(p):
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    return p


def h1(t):
    return _con_siguiente(P(t, 11.5, True, align=WD_ALIGN_PARAGRAPH.LEFT, before=16, after=6,
                            caps=True, track=16))


def h2(t):
    return _con_siguiente(P(t, 10.5, True, align=WD_ALIGN_PARAGRAPH.LEFT, before=10, after=4,
                            color=TINTA_SUAVE))


def etiqueta(t, after=3):
    return _con_siguiente(P(t, 10, True, align=WD_ALIGN_PARAGRAPH.LEFT, after=after,
                            caps=True, track=14, color=TINTA_SUAVE))


def figure(fn, label, caption, ancho=155):
    # Springer: ninguna puntuacion al final del pie
    assert not caption.rstrip().endswith((".", ";", ":")), label
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(os.path.join(FIG, fn), width=Mm(ancho))
    p.paragraph_format.keep_with_next = True
    _sin_numero(p)
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    q.paragraph_format.space_after = Pt(12)
    q.paragraph_format.line_spacing = 1.1
    q.paragraph_format.keep_together = True
    run(q, label + " ", 9, bold=True)
    run(q, caption, 9, color=GRIS_PIE)


def table(label, caption, cols, rows, widths=None, size=8.5):
    q = doc.add_paragraph()
    q.paragraph_format.space_before = Pt(10)
    q.paragraph_format.space_after = Pt(4)
    q.paragraph_format.line_spacing = 1.1
    run(q, label + " ", 9, bold=True)
    run(q, caption, 9, color=GRIS_PIE)
    q.paragraph_format.keep_with_next = True
    q.paragraph_format.keep_together = True
    t = doc.add_table(rows=1 + len(rows), cols=len(cols))
    t.alignment = 1
    for j, c in enumerate(cols):
        cell = t.rows[0].cells[j]
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(cell.paragraphs[0], c, size, bold=True)
        _sombrea(cell)
        _borde_celda(cell, {"top": 12, "bottom": 6})
    ultima = len(rows) - 1
    for i, fila in enumerate(rows):
        for j, v in enumerate(fila):
            cell = t.rows[1 + i].cells[j]
            cell.paragraphs[0].alignment = (WD_ALIGN_PARAGRAPH.LEFT if j == 0
                                            else WD_ALIGN_PARAGRAPH.CENTER)
            run(cell.paragraphs[0], str(v), size)
            _borde_celda(cell, {"bottom": 12} if i == ultima else {})
    # las filas no se parten entre paginas y la cabecera se repite
    for fila in t.rows:
        trPr = fila._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    if widths:
        assert sum(widths) <= 160, "tabla de %d mm" % sum(widths)
        t.autofit = False
        for j, w in enumerate(widths):
            t.columns[j].width = Mm(w)
            for fila in t.rows:
                fila.cells[j].width = Mm(w)
    e = doc.add_paragraph()
    e.paragraph_format.space_after = Pt(2)
    _sin_numero(e)


def _campo_pagina(p):
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

_ln = OxmlElement("w:lnNumType")
_ln.set(qn("w:countBy"), "1")
_ln.set(qn("w:restart"), "continuous")
sec._sectPr.append(_ln)

# ------------------------------------------------------ nombres en ingles
MUTANTE_EN = {
    "curvatura_restada": "Curvature subtracted",
    "sin_curvatura": "Curvature omitted",
    "altura_objetivo_nula": "Target height zero",
    "extremos_incluidos": "Endpoints included",
    "muestreo_grueso": "Coarse profile sampling",
}
PRUEBA_EN = {
    "plano a 3 km: se ve": "plane at 3 km: visible",
    "barrera de 50 m a 6 km: tapa": "50 m barrier at 6 km: blocks",
    "barrera rebajada a 1 m a 3 km: no tapa": "barrier lowered to 1 m at 3 km: does not block",
    "depresion a 3 km: nunca tapa": "depression at 3 km: never blocks",
    "barrera de 2 m: no tapa a 3 km": "2 m barrier at 3 km: does not block",
    "la misma barrera de 2 m si tapa a 9 km": "same 2 m barrier at 9 km: blocks",
    "barrera de una sola celda a 3 km: tapa igual": "one-cell barrier at 3 km: still blocks",
    "objetivo a ras de suelo tras loma de 12 m a 4 km: no se ve":
        "ground-level target behind a 12 m rise at 4 km: not visible",
    "mismo caso con objetivo de 30 m: se ve": "same case, 30 m target: visible",
    "observador sobre una cima: no se tapa a si mismo": "observer on a summit: does not block itself",
    "objetivo sobre una cima: sigue viendose": "target on a summit: still visible",
    "plano a 1 km: la curvatura no cambia nada": "plane at 1 km: curvature changes nothing",
    "plano a 40 km: mas alla del horizonte geometrico": "plane at 40 km: beyond the geometric horizon",
    # propiedades vigentes
    "reciprocidad con alturas intercambiadas": "reciprocity with swapped heights",
    "obstaculo dominante en cualquier celda interior": "dominant obstacle at any interior cell",
    "distancia critica derivada sobre plano": "derived critical distance over a plane",
    "alturas: subir nunca quita vista y basta para ver":
        "raising a height never removes a view and eventually yields one",
    # propiedades de la primera version
    "reciprocidad de la vision": "reciprocity with equal heights",
    "monotonia en la altura del observador": "monotonicity in observer height",
    "monotonia en la distancia sobre plano": "monotonicity in distance over a plane",
    "monotonia en la altura de la barrera": "monotonicity in barrier height",
}


def prueba_en(nombre):
    m = re.match(r"plano justo por debajo de la distancia critica \(([\d.]+) km\): se ve$", nombre)
    if m:
        return "plane just inside the critical distance (%s km): visible" % m.group(1)
    m = re.match(r"plano bien por encima de la critica \(([\d.]+) km\): la curvatura tapa$", nombre)
    if m:
        return "plane well beyond the critical distance (%s km): blocked" % m.group(1)
    return PRUEBA_EN[nombre]      # KeyError si aparece una prueba nueva sin traducir


def rasgo_en(c):
    """El rasgo que el caso pretende probar, descrito desde su geometria."""
    t, alt, ancho, pos = (c["terreno"], c["altura_rasgo_m"], c["ancho_rasgo_celdas"],
                          c["posicion_rasgo_km"])
    if c["rasgo"].startswith("objetivo de"):
        return "%s m target height" % g(c["h_tgt"])
    if t == "plano":
        return "Earth curvature"
    if t == "barrera":
        return "%s m barrier, %d cell%s wide, at %s km" % (g(alt), ancho, "" if ancho == 1 else "s",
                                                           f(pos, 2))
    if t == "depresion":
        return "%s m depression, %d cells wide" % (g(-alt), ancho)
    if t == "cima":
        return "%s m summit under the %s" % (g(alt), "observer" if pos == 0 else "target")
    raise ValueError(t)


# casos citados por su nombre en el texto
C_BAR50 = caso("barrera de 50 m a 6 km: tapa")
C_BAR2 = caso("la misma barrera de 2 m si tapa a 9 km")
C_LOMA = caso("objetivo a ras de suelo tras loma de 12 m a 4 km: no se ve")
C_30 = caso("mismo caso con objetivo de 30 m: se ve")
H_OBS, H_TGT = DCRIT["h_obs"], DCRIT["h_tgt"]

# ================================================================== title page
P("Reproducible and wrong", 19, True, align=WD_ALIGN_PARAGRAPH.CENTER,
  before=10, after=2, track=10)
P("Silent failures in archaeological visibility analysis and a benchmark to catch them",
  12, align=WD_ALIGN_PARAGRAPH.CENTER, after=0, color=TINTA_SUAVE, italic=True)
_regla = doc.add_paragraph()
_regla.paragraph_format.space_before = Pt(10)
_regla.paragraph_format.space_after = Pt(12)
_borde_parrafo(_regla, "bottom", sz=8, espacio=1)
_sin_numero(_regla)

P(AUTOR, 11, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
P(FILIACION, 9.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, color=TINTA_SUAVE)
P("Corresponding author: %s. ORCID: https://orcid.org/%s" % (CORREO, ORCID_A),
  9, align=WD_ALIGN_PARAGRAPH.CENTER, after=16, color=TINTA_SUAVE)

etiqueta("Abstract")
ABSTRACT = (
    "Computational reproducibility guarantees that an analysis can be re-run and will return the "
    "same result. It does not guarantee that the result is true: a reproducible pipeline reproduces "
    "its errors faithfully. This paper characterises a class of defects in archaeological visibility "
    "analysis that raise no error, produce plausible output, survive peer review and "
    "re-execution, and invert or erase the conclusion of the study containing them. Three, "
    "documented in a recent intervisibility study of the Titicaca basin, are reproduced under "
    "controlled conditions. Two instruments are presented. The first is an executable benchmark for "
    "line-of-sight engines (%d terrain cases with derived expectations and %d behavioural properties) "
    "whose adequacy is measured by mutation analysis, which showed that its first-version "
    "properties detected none of the injected defects. The second is a "
    "synthetic-landscape laboratory in which the truth is known by construction. There, sampling null "
    "placements over water destroys statistical power (%s %% against a ceiling of %s %%) without "
    "raising false positives, and a tightly cropped sampling region biases the contrast in a "
    "direction set by how the sites align with the terrain grain (Spearman's "
    "ρ = %s) yet passes a marginal calibration audit. Two inexpensive "
    "diagnostics flag both. Two widely installed programs, gdal_viewshed and r.viewshed, "
    "pass every case when configured deliberately; at their shipped defaults both fail, "
    "disagreeing on %d cases and returning the same wrong verdict on %d others. Agreement between "
    "programs validates nothing. Reproducibility certifies the transport of a computation; "
    "validation certifies its content. The discipline needs both."
    % (N_CASOS, N_PROPS, pct(RESU["S1"]["agua"]["rechazo"]), pct(POT_TEO),
       f(MEC["spearman_desalineacion"], 2), N_DISC, N_COMPARTIDO))
assert 150 <= len(ABSTRACT.split()) <= 250, "resumen de %d palabras" % len(ABSTRACT.split())
P(ABSTRACT, after=8, size=9.5)
_borde_parrafo(doc.paragraphs[-1], "left")
doc.paragraphs[-1].paragraph_format.left_indent = Cm(0.35)

etiqueta("Keywords")
P("viewshed analysis; software validation; mutation testing; computational reproducibility; "
  "null models; geographic information systems", after=18, size=9.5, italic=True,
  color=TINTA_SUAVE)

# ================================================================ introduction
h1("1 Introduction")

P("Archaeology has spent a decade building the case for computational reproducibility. The argument "
  "has largely been won: analyses should ship their code and data, be version-controlled, and re-run "
  "from top to bottom on demand (Marwick, 2017; Peng, 2011; Sandve et al., 2013). The case was made "
  "in this journal with a worked example (Marwick, 2017), and it has since informed how "
  "archaeological science is done and reported (Schmidt & Marwick, 2020). This paper is about what "
  "that programme, on its own, cannot deliver. Re-running an analysis verifies that the code "
  "produces the reported numbers; it says nothing about whether the numbers are right. A pipeline "
  "with an inverted sign is perfectly reproducible. It reproduces the inverted sign. Leek and Peng "
  "(2015) made the point for data analysis in general: reproducible research can still be wrong, "
  "and errors are better prevented than merely exposed after publication.")

P("The distinction has become sharper as the reproducibility agenda has matured. A survey of "
  "1,576 scientists found that more than 70 % had failed to reproduce another scientist's results "
  "and more than half their own (Baker, 2016); an audit of 204 articles in a journal with a "
  "data-and-code policy could obtain the materials behind only 44 % of them and reproduce the "
  "findings of 26 % (Stodden et al., 2018); and reviews of the computing literature catalogue the "
  "many layers (environment, dependencies, numerical libraries) at which a re-execution can quietly "
  "diverge (Ivie & Thain, 2018). Geography and geographic information science have taken up the "
  "agenda for spatial analysis specifically (Brunsdon, 2016; Nüst & Pebesma, 2021), and Kedron et "
  "al. (2021) have carried into geospatial research the distinction, formalised by the National "
  "Academies of Sciences, Engineering, and Medicine (2019), between reproducibility (the same data "
  "and code return the same result) and replicability (new data return the same finding). Neither "
  "guarantee is validity. A study can be reproducible, replicable and wrong, if the defect lives in "
  "the shared procedure.")

P("The defects that matter here are of a specific kind. A sign error in a data-processing script "
  "forced the retraction of five protein-structure papers, three of them in Science (Miller, 2006). "
  "A spreadsheet coding error, compounded by undeclared choices of data exclusion and weighting, "
  "propped up an influential claim about public debt and growth for three years before anyone "
  "re-derived the numbers (Herndon et al., 2014). In neuroimaging, a long-standing software bug "
  "and default settings whose statistical assumptions did not hold inflated the false-positive "
  "rates of cluster inference in widely used packages (Eklund et al., 2016).")
P("Merali (2010) and "
  "Soergel (2015) argue that software faults of this kind are common enough to undermine results "
  "across computational science generally. Hatton and Roberts (1994) had already shown, by handing "
  "the same seismic data and parameters to nine independently written processing packages, that "
  "their results disagreed by margins that grew with the size of the code and were systematic "
  "rather than random. What makes these cases instructive is not that software failed but how it "
  "failed: no crash, no warning, output of entirely plausible appearance.")

P("Archaeological visibility analysis, a methodological tradition reviewed by Lake and Woodman "
  "(2003) and critically examined by Wheatley and Gillings (2000) and Gillings (2015, 2017), is "
  "unusually exposed to this failure mode. A viewshed or intervisibility computation returns maps "
  "and networks that look reasonable under almost any defect, and there is no ground truth on real "
  "terrain against which to notice that they are wrong. Fisher (1993) showed three decades ago that "
  "independent implementations of the same viewshed disagree substantially without any of them "
  "being obviously broken, and Riggs and Dean (2007) confirmed against a field-surveyed viewshed "
  "that part of that disagreement comes from the packages' algorithms rather than from the "
  "elevation data. Reviewers, as a rule, see results, not code, so review does not catch the "
  "defect. Reproduction re-executes the same code, so reproduction does not catch it either. The "
  "defect passes through both of the controls on which the discipline currently relies.")

P("A recent intervisibility study of %d archaeological sites in the Titicaca basin documented "
  "three such defects encountered, and corrected, during its own analysis (deposited as Mamani "
  "Calisaya et al., 2026; the study itself is reported in a separate manuscript). The sign of the "
  "Earth-curvature correction was inverted, which renders the Earth concave and lets no relief "
  "block any long-range view. The elevation model assigned a constant elevation to the lake, a "
  "perfect plane covering %s %% of the study area that blocked nothing and inflated the null model "
  "until a real effect vanished (z = %s before the lake was masked, against z = %s after)."
  % (N_SITIOS_CAMPO, pct(AGUA_CAMPO, 1), fz(Z_CAMPO_AGUA), fz(Z_CAMPO_OK)))
P("Finally, the field study reports that a tightly fitted raster crop, in which the lake covered %s %% of the "
  "area, admitted only %d of the %d orientations of the rigid null model (which relocates the "
  "observed site configuration as a rigid body, translating and rotating it), inflating the "
  "contrast from z = %s to z = %s. None of the three produced any visible failure. Each was found "
  "by accident or by a purpose-built check, not by inspection of results."
  % (pct(AGUA_RECORTE, 1), ORIENT_CAMPO, ORIENT_TOTAL_CAMPO, fz(Z_CAMPO_OK), fz(Z_CAMPO_RECORTE)))

P("This paper treats that episode as a specimen and builds the instruments the discipline lacks. "
  "It makes five contributions. The first is a characterisation of the silent failure class and a "
  "two-level taxonomy (defects of the geometric engine versus defects of the analysis design) with "
  "six concrete defects, each documented in the field or shipped as a default or a plausible "
  "shortcut, and one candidate that proved harmless. The second is an executable benchmark for "
  "line-of-sight engines whose adequacy is itself measured by mutation analysis rather than "
  "asserted; the measurement caught the benchmark's own first set of behavioural properties passing "
  "every defective engine. The third is a synthetic-landscape laboratory in which the truth is "
  "known by construction, so that the damage each design defect does to statistical inference is "
  "measured exactly.")
P("The fourth is a measurement of two widely used, freely available production "
  "engines against the same benchmark, which shows that the defect need not be in the code at all "
  "and that two programs agreeing with each other proves nothing. The fifth is a pair of "
  "diagnostics that detect the two documented design defects at negligible cost before any real terrain is "
  "touched, together with six practices and a list of the parameters that every visibility study "
  "should declare.")

# ================================================================= background
h1("2 Background")
h2("2.1 Uncertainty in viewshed computation")
P("The archaeological literature has known for 30 years that a viewshed is not a fact about the "
  "terrain but an output of a procedure. Fisher (1993) computed the same viewshed with several "
  "geographic information system (GIS) packages and found that the areas they returned differed "
  "by margins that no analyst would tolerate in a measurement, without any package being "
  "demonstrably wrong. He called this ‘algorithm and implementation uncertainty’, distinguished it "
  "from the uncertainty of the elevation model itself, and traced it to three choices that GIS "
  "documentation rarely states: how elevations are inferred from the grid, how viewpoint and target "
  "are represented, and how the comparison is formulated. The second alone moved the visible area "
  "by up to 50 %, and it is the parameter at issue in Section 4.5. He closed by calling for "
  "‘standards and/or empirical benchmark datasets for GIS functions’, a call this paper answers "
  "for the line of sight.")
P("Nackaerts et al. (1999) propagated elevation error into probabilistic viewsheds by Monte Carlo "
  "simulation and gave the resulting maps a stated accuracy, and Riggs and Dean (2007), comparing "
  "predicted viewsheds with a field-surveyed one, found elevation error to be the largest source of "
  "discrepancy but confirmed that the differing algorithms of GIS packages also contribute "
  "significantly and yield viewsheds that disagree with one another. Kormann and Lock (2014) "
  "examined the effect of curvature and refraction on archaeological visibility studies and found "
  "that, within a 10 km range, applying both terms reduced the visible area of their Danebury "
  "landscape by about 20 %, which is the regime in which the field defects reproduced here operate.")
P("The response of the archaeological community to this uncertainty has been, in the main, to "
  "model it rather than to eliminate it. Probable and fuzzy viewsheds propagate elevation error "
  "into a graded map (Fisher, 1995); cumulative and total viewsheds, and the visualscapes of "
  "Llobera (2003), move from single lines of sight to the visual structure of a whole landscape; "
  "and the turn to networks, which treats intervisibility as a graph and models the dependence "
  "between its edges with exponential random graph models (Brughmans & Brandes, 2017; Brughmans "
  "et al., 2015), moves the inference to a level where individual lines of sight matter less. "
  "Ogburn (2006) showed that the size of an object and its distance decide whether it can be "
  "discerned at all, which makes the height of the target an archaeological variable rather than "
  "a technical default.")
P("Lake et al. (1998) showed early on that the software itself could be tailored to the "
  "archaeological question, and Čučković (2016) published a freely available plug-in for "
  "visibility analysis in QGIS (originally Quantum GIS), with a line-of-sight engine of its own. "
  "Ducke (2012) argued that free and open-source software removes the ‘black box’ that proprietary "
  "tools place between an analysis and its algorithms. What none of this work provides is a way to "
  "decide whether a given engine, with a given configuration, is correct. The disagreement Fisher "
  "observed is treated as a property of the operation, when much of it is the signature of defects "
  "that a benchmark could attribute to one implementation or the other.")
P("The design level has received the same kind of attention. Lake and Woodman (2003) and Wheatley "
  "and Gillings (2000) argued that the null model against which an observed visibility pattern is "
  "tested decides the result as much as the pattern does, and that random points drawn from the "
  "whole landscape are the wrong comparison when sites share topographic traits. The field study "
  "behind this paper followed that advice and still went wrong twice at the design level, in ways "
  "the advice does not anticipate: not in which null to use, but in where the null was allowed to "
  "sample. That is the gap the landscape laboratory of Section 3.4 addresses.")

h2("2.2 Correctness of scientific software and the oracle problem")
P("Software engineering has a name for the difficulty at the centre of this paper. Testing a "
  "program requires an oracle, a way of knowing what the correct output is, and scientific software "
  "is written precisely to compute answers that nobody knows in advance. Kanewala and Bieman (2014) "
  "reviewed the literature on testing scientific software and placed the oracle problem first among "
  "the obstacles peculiar to it, and Hatton (1997), synthesising the experiments of Hatton and "
  "Roberts (1994), described mature scientific codes that, given identical inputs, produced results "
  "whose spread grew with every stage of the computation.")
P("The field has three answers to the oracle problem, and this paper applies all of them to "
  "visibility analysis. The first is to derive expectations from theory where a closed form exists, "
  "so that the test knows the answer for a reason and not by assertion. The second is metamorphic "
  "testing (Chen et al., 2018; Segura et al., 2016): instead of asking what the output should be, "
  "ask how the output must change when the input changes in a known way (raising the observer can "
  "never remove a line of sight) and check the relation over many random inputs, in the manner of "
  "property-based testing (Claessen & Hughes, 2000). Such relations are necessary conditions, not "
  "sufficient ones: a defective engine satisfies every relation that does not engage its defect, "
  "and Section 4.2 shows that the risk is not hypothetical.")
P("The third answer measures the tests themselves. A suite that the correct program passes proves "
  "little; the question is whether it would fail a defective one. Mutation analysis, also called "
  "mutation testing (DeMillo et al., 1978; Jia & Harman, 2011), answers exactly this by injecting "
  "known defects and counting how many the suite detects, and it carries a subtlety that matters "
  "here: some mutations do not change observable behaviour at all, and a suite must not be blamed "
  "for failing to detect what cannot be detected. None of these techniques is new to software "
  "engineering, and Hook and Kelly (2009) had already used mutation to judge the tests of "
  "scientific software. What this paper adds is their application to a geometric computation in "
  "archaeology, and the finding, reported in Section 4.2, that the expectations and properties "
  "written by hand to check such a computation fail in the same silent way as the code they are "
  "meant to check.")

h2("2.3 The failure class")
P("A silent failure, as the term is used here, is a defect with four properties: it raises no "
  "error and produces no visibly malformed output; its output is plausible and interpretable, "
  "statistics included; it survives both peer review (which sees results, not code) and "
  "computational reproduction (which re-executes the defect); and it changes the substantive "
  "conclusion of the study. The last clause is what separates a silent failure from a tolerable "
  "approximation: the defects studied here do not perturb the result; they invert or erase it.")

P("Two levels must be distinguished, because they demand different instruments. Engine defects "
  "live in the geometric computation itself: a wrong sign, a missing correction, an ill-chosen "
  "default, a sampling shortcut. Design defects live above a perfectly correct engine, in how the "
  "null model is constructed and where it is allowed to sample. Table 1 lists the six defects "
  "treated in this paper and one candidate that proved harmless. Every engine defect is either "
  "documented in the field episode or a default or shortcut that mainstream software makes easy; "
  "Section 4.5 shows that two of them are the shipped defaults of two widely used engines. Both "
  "design defects are documented. The harmless candidate, which includes the endpoint cells in the "
  "blocking test, is kept because a benchmark must be able to tell a harmless change from a "
  "harmful one (Section 4.1).")

table("Table 1", "Defects studied. The first five candidates are injected into the line-of-sight "
      "engine, the last two into the design of the null-model contrast. ‘Documented’ means observed "
      "and quantified in the Titicaca field study; ‘shipped default’ means the behaviour of the "
      "production engines gdal_viewshed and r.viewshed run with only their mandatory arguments "
      "(Section 4.5). The fourth candidate "
      "proved equivalent to the reference engine and is therefore not a defect",
      ["Defect", "Level", "Mechanism", "Status"],
      [["Curvature subtracted", "engine", "Earth rendered concave", "documented"],
       ["Curvature omitted", "engine", "defensible only at short range",
        "shipped default (r.viewshed)"],
       ["Target height zero", "engine", "monument treated as a point on the ground",
        "shipped default (both engines)"],
       ["Endpoints included", "engine", "endpoint cells enter the blocking test",
        "provably equivalent (Section 4.1)"],
       ["Coarse profile sampling", "engine", "narrow barriers fall between samples",
        "plausible shortcut"],
       ["Water left unmasked", "design", "a flat lake that blocks nothing feeds the null",
        "documented"],
       ["Tightly cropped sampling region", "design",
        "null loses orientations that do not fit", "documented"]],
      widths=[40, 13, 63, 44])

# ==================================================================== methods
h1("3 Materials and methods")
P("The architecture is summarised in Fig. 1. Two instruments answer two different questions, "
  "whether the geometry is right and whether the inference is right, and converge on one rule: "
  "only a validated engine and a diagnosed design touch real terrain.")
h2("3.1 A line-of-sight engine with switchable defects")
P("The reference engine evaluates the line of sight between two cells of a digital elevation "
  "model (DEM) by sampling the intervening terrain at one sample per cell and testing whether it "
  "rises above the straight line joining observer and target. Earth curvature and atmospheric "
  "refraction are combined in an effective radius R = Rₑ/(1 − k), with Rₑ = %s km "
  "and k = %s; when gdal_viewshed and r.viewshed apply refraction, their default coefficient is 1/7, about %s. Written with respect to "
  "the chord between the endpoints, the correction term d(D − d)/2R, where D is the distance "
  "between the endpoints and d the distance from the observer along the profile, is added to the "
  "intervening terrain, because seen from that chord the Earth bulges between the endpoints and "
  "the bulge vanishes at them."
  % (f(R_EARTH / 1000, 0), f(K_REFRACTION, 2), f(RD["refraction_coeff"], 3)))
P("Subtracting the term, as the customary phrase ‘drop due to "
  "curvature’ suggests, is the first defect (Fig. 2a–b). Each of the five engine candidates "
  "of Table 1 can be switched on by name; this is what makes the adequacy of the benchmark "
  "measurable (Section 3.3). The engine and every experiment below depend only on NumPy.")

h2("3.2 Test cases with derived expectations and behavioural properties")
P("The benchmark has two parts. The first consists of %d terrain cases whose correct answer is "
  "known in advance (Table 2): a plane at short range, barriers that must and must not block, a "
  "depression that can never block, observer and target standing on their own summits, a "
  "ground-level target and a %s m monument behind the same rise, and planes bracketing the critical "
  "distance at which curvature alone severs the view. All cases are profiles along one row of a "
  "grid of %s m cells. The critical distance is not written by hand. Over a plane, the straight "
  "line between observer and target grazes the curvature bulge when D equals the sum of the two "
  "horizon distances, √(2Rhₒ) + √(2Rhₜ), which for the default observer and "
  "target heights hₒ = %s m and hₜ = %s m gives %s km; the cases probe both sides of that "
  "derived value."
  % (N_CASOS, g(C_30["h_tgt"]), g(CELDA), g(H_OBS), g(H_TGT), f(D_CRIT_KM, 1)))
figure("fig_pipeline.png", "Fig. 1",
       "The validation pipeline. Left, the engine level: a line-of-sight engine with five "
       "switchable defects is run against a benchmark of terrain cases with derived expectations "
       "and behavioural properties, and the benchmark itself is audited by mutation analysis. "
       "Right, the design level: synthetic landscapes in which the truth is known by construction "
       "are used to measure what each design defect does to calibration and power. Both levels "
       "feed two diagnostics. S0 and S1 are the no-effect and real-effect scenarios of Section 3.4 (K, the number "
       "of random placements from which S1 takes the best), D1 and D2 the diagnostics of Section "
       "3.5, and DEM stands for digital elevation model", ancho=145)

P("Every case is of one of two kinds. In a feature case the verdict must be decided by the feature "
  "the case is named after; in a control it must not. The benchmark enforces the distinction "
  "mechanically: each case is re-run with its feature removed (the barrier or depression "
  "flattened, the target lowered to the ground, or the curvature term switched off), and the "
  "verdict must change for a feature case and stay the same for a control. Of the %d cases, %d are "
  "feature cases and %d are controls, and all pass the check. The reason for this discipline "
  "appears in Section 4.2." % (N_CASOS, RASGO["casos_de_rasgo"], RASGO["controles"]))
P("The second part consists of %s behavioural properties, each checked with fixed seeds on random "
  "rugged terrains or random heights (%s evaluations in all). Visibility is reciprocal when the "
  "observer and target heights are swapped together with the direction of sight. Raising any "
  "interior cell never unblocks a view, and a cell raised far above the whole terrain blocks "
  "wherever it stands. Over a plane, with randomly drawn heights, a line of sight is clear just "
  "inside the derived critical distance and blocked just and well beyond it. Raising the observer "
  "or the target never removes a view and, doubled often enough, always produces one. These are "
  "metamorphic relations in the sense of Section 2.2 (Chen et al., 2018; Segura et al., 2016), "
  "checked in the manner of property-based testing (Claessen & Hughes, 2000). Unlike a case, a "
  "property has no single configuration to be accidentally right about, but it is only as strong "
  "as the defects it engages; the four used here replaced a first set that engaged none "
  "(Section 4.2)." % (num(N_PROPS), "{:,}".format(N_EVAL_PROPS)))

table("Table 2", "The %d benchmark cases. D, distance between observer and target; hₒ and "
      "hₜ, observer and target heights above the ground. A feature case must change its "
      "verdict when its feature is removed; a control must not. All cases use %s m cells, and the "
      "expected verdict is part of each name" % (N_CASOS, g(CELDA)),
      ["Case and expected verdict", "Feature", "D (km)", "hₒ / hₜ (m)", "Role"],
      [[prueba_en(c["prueba"]), rasgo_en(c), f(c["distancia_km"], 2),
        "%s / %s" % (g(c["h_obs"]), g(c["h_tgt"])),
        "feature case" if c["tipo"] == "rasgo" else "control"]
       for c in CASOS],
      widths=[62, 44, 14, 18, 22], size=8)

h2("3.3 Mutation analysis: measuring the benchmark itself")
P("A benchmark that the reference engine passes proves little; the question is whether it would "
  "fail a defective one. Mutation analysis answers exactly this (DeMillo et al., 1978; Jia & "
  "Harman, 2011): each engine candidate of Section 3.1 is switched on in turn and the full "
  "benchmark is run against the mutated engine, recording separately which cases and which "
  "properties detect it. A candidate that no test detects marks a hole in the benchmark, unless "
  "the mutation does not alter observable behaviour at all; in that case it is an equivalent mutant "
  "and detecting it is impossible in principle. The two situations are distinguished by argument "
  "where one is available and empirically in any case, by sweeping the mutant against the reference "
  "engine over thousands of random terrain pairs and endpoint configurations. The first version of "
  "the properties was run against every mutant as well, so that its detection rate could be "
  "reported.")

h2("3.4 A landscape laboratory with ground truth by construction")
P("Engine defects can be caught by geometry. Design defects cannot: they operate above a correct "
  "engine, and on real terrain there is no way to know what the contrast should have concluded. "
  "The laboratory therefore manufactures landscapes where the truth is known exactly. Each "
  "replicate generates an anisotropic synthetic terrain (ridges with a dominant, randomised grain "
  "direction) with a lake occupying on average %s %% of the map, built the way real elevation "
  "models build lakes: by flooding a basin to a constant elevation (Fig. 3a)."
  % pct(DIAG["agua_fraccion_celdas_media"]))
P("An elongated cloud of %d sites is then placed under two scenarios. In scenario S0 the cloud is "
  "placed by the very rules the rigid null model uses to place its own draws; observed and null "
  "placements are then exchangeable, and the p value of a correct contrast is uniform by symmetry "
  "(exactly so, up to ties in the discrete density, which can only make the test conservative). "
  "Every measured departure from uniformity is therefore attributable to the procedure, not to "
  "chance. In scenario S1 the cloud is placed at the best of K = %d random placements, which makes "
  "the hypothesis under test, that the cloud is sited where it sees more than the same "
  "configuration would elsewhere, true by construction; the theoretical power of a correct "
  "contrast follows from rank symmetry and is computed alongside the experiment."
  % (CFG["n_sitios"], CFG["k_mejor"]))
P("The statistic is "
  "the density of the complete intervisibility network of the cloud, standardised as z against "
  "the null placements. The contrast is one-sided (higher density than the null), with "
  "p = (b + 1)/(N + 1), where b is the number of null placements at least as dense as the observed "
  "cloud and N the number of null placements (Phipson & Smyth, 2010), as in the field study.")
P("Each replicate then runs the same contrast three times on identical data: with the correct "
  "design, with null placements allowed onto the water, and with the null sampling region cropped "
  "to the bounding box of the observed cloud plus %d cells. The design is paired: any difference "
  "between procedures is attributable to the defect and to the Monte Carlo noise of independent "
  "null sets, whose contribution to a difference in z is of order 1/√N (about %s for N = %d). "
  "In total, %d replicates were run, each with N = %d null placements per contrast."
  % (CFG["margen_ajustado_celdas"], f(RUIDO_MC, 2), N_NULL, R_, N_NULL))

h2("3.5 Diagnostics")
P("Two checks are computed in every run, neither requiring ground truth. D1, placement validity: "
  "the fraction of accepted null placements with at least one site on water, which in a sound "
  "design is identically zero. D2, orientation coverage: the fraction of the %d placement "
  "orientations, one per degree, that fit geometrically inside the sampling region (Fig. 3b–c), "
  "which in a sound design is 100 %%. Both cost almost nothing to compute, and either would have "
  "flagged its corresponding field defect before a single line of sight was calculated."
  % CFG["pasos_orientacion"])

h2("3.6 Production engines under the same benchmark")
P("The instruments above are built around an engine written for this study, which shows that the "
  "benchmark can detect defects but says nothing about the production software that archaeologists "
  "use. The %d terrain cases were therefore materialised as small georeferenced rasters and passed "
  "directly to the command-line programs of two production engines shipped with QGIS %s: "
  "gdal_viewshed of the Geospatial Data Abstraction Library (GDAL) version %s (GDAL/OGR "
  "contributors, 2026), and r.viewshed of the Geographic Resources Analysis Support System (GRASS) "
  "version %s (GRASS Development Team, 2026), which implements the sweep algorithm of Haverkort et "
  "al. (2009). The QGIS processing dialogues that wrap these programs have defaults of their own, "
  "which were not measured."
  % (N_CASOS, _G["distribucion"].replace("QGIS ", ""), _G["version_gdal"], _R["version"]))
P("Each engine was run in two ways on every case. Configured, every parameter was set to the value "
  "this study uses: observer and target heights equal to those of the case (Table 2); for "
  "gdal_viewshed, the curvature coefficient ‑cc %s, that is, 1 − k; for r.viewshed, the "
  "curvature flag ‑c and the refraction flag ‑r with refraction_coeff = %s. With ‑c, "
  "r.viewshed takes the Earth radius from the ellipsoid of the location, here %s m rather than the "
  "%s m of the reference engine, which moves its critical distance over a plane by about %s m and "
  "alters no verdict."
  % (f(1 - K_REFRACTION, 2), f(K_REFRACTION, 2), "{:,}".format(A_ELIPSOIDE).replace(",", " "),
     "{:,}".format(int(R_EARTH)).replace(",", " "), f(DIF_RADIO_M, 0)))
P("At shipped defaults, each program received only its mandatory arguments: the "
  "input raster, the output raster and the observer coordinates. That leaves gdal_viewshed with an "
  "observer height of %s m, a target height of %s m and a curvature coefficient of %s, and "
  "r.viewshed with %s m, %s m and neither curvature nor refraction. To attribute each failure, the "
  "shipped run was repeated with one of the study's parameters restored at a time. The verdict of "
  "each run was read back from the output raster at the target cell and compared with the derived "
  "expectation of the case. Nothing in the benchmark was adapted to either engine: the cases are "
  "the same grids the reference engine is tested on."
  % (g(GD["oz"]), g(GD["tz"]), g(GD["cc"]), g(RD["observer_elevation"]), g(RD["target_elevation"])))

h2("3.7 Software and tooling")
P("The analysis code depends on NumPy alone; Matplotlib is used for the figures and python-docx for "
  "the manuscript, which is generated from the result files so that no number derived from a "
  "computation is typed by hand. An automated audit, deposited with the code, checks every such "
  "number in the text against the result file it comes from. In accordance with the journal's "
  "policy on large language models (LLMs), the author declares that Claude (Anthropic), an LLM, "
  "was used as a coding and drafting assistant during the development of the analysis code, the "
  "figures and the text. Every line of code was reviewed by the author and is exercised by the "
  "deposited benchmark and audits, every result was recomputed from the deposited scripts, and the "
  "author takes full responsibility for the content of the article.")

# ==================================================================== results
h1("4 Results")

h2("4.1 The benchmark and its mutation matrix")


def _lista(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def _muerte(d):
    v = MUT[d]
    props = [PRUEBA_EN[p] for p in v["cuales_propiedades"]]
    return "%s by %s of the %d cases and by %s" % (
        MUTANTE_EN[d].lower(), num(v["casos_que_saltan"]), N_CASOS,
        ("the property ‘%s’" % props[0]) if len(props) == 1 else
        "%s properties (%s)" % (num(len(props)), _lista(["‘%s’" % p for p in props])))


P("The reference engine passes all %d tests (%d cases and %s properties). Table 3 gives the "
  "mutation matrix. Every candidate with observable consequences is detected by at least one case "
  "and by at least one property that tests something different: %s. Fig. 2 dissects two of the "
  "detected (‘killed’) mutants on single terrain profiles: in each panel the defective verdict is "
  "exactly as plausible to the eye as the correct one, which is the failure class made visible."
  % (N_TESTS, N_CASOS, num(N_PROPS), "; ".join(_muerte(d) for d in NO_EQUIV)))
table("Table 3", "Mutation matrix: for each engine candidate, how many of the %d cases and of the "
      "%d current properties detect it, how many of the %d first-version properties did, and which "
      "current property kills it" % (N_CASOS, N_PROPS, len(PV1["nombres"])),
      ["Engine candidate", "Cases failing", "Properties failing",
       "First-version properties failing", "Killed by property"],
      [[MUTANTE_EN[d], frac(MUT[d]["casos_que_saltan"], MUT[d]["de_casos"]),
        frac(MUT[d]["propiedades_que_saltan"], MUT[d]["de_propiedades"]),
        frac(len(PV1["cuales_por_mutante"][d]), len(PV1["nombres"])),
        ("; ".join(PRUEBA_EN[p] for p in MUT[d]["cuales_propiedades"])
         if MUT[d]["cuales_propiedades"] else "none: provably equivalent")]
       for d in MUT],
      widths=[36, 20, 22, 26, 56])

P("The exception is instructive. Including the endpoint cells in the blocking test, a plausible "
  "off-by-one error, is behaviourally equivalent to the reference engine, and the equivalence is "
  "provable: the curvature term vanishes at both endpoints, so the blocking test there reduces to "
  "hₒ ≥ 0 and hₜ ≥ 0, which always holds. The sweep of Section 3.3 confirms it, "
  "with no difference in any of %s paired evaluations, and the equivalence breaks, as the argument "
  "predicts, once a height is negative: with the observer %s m below the ground at the edge of an "
  "escarpment, the reference engine sees a target %s km away that the mutant declares blocked. The "
  "distinction matters: mutation analysis without an equivalence check would count the candidate as "
  "a hole, making the benchmark look weaker than it is (Jia & Harman, 2011). Of the seven "
  "candidates of Table 1, then, six are defects and the seventh is harmless."
  % ("{:,}".format(_EQ["comparaciones_equivalencia"]), g(-CONTRA["h_obs"]),
     f(CONTRA["distancia_km"], 2)))

figure("fig_anatomia.png", "Fig. 2",
       "Anatomy of a silent failure. (a) The reference engine finds this %s km line of sight "
       "blocked: with curvature and refraction applied, the deciding relief rises less than three "
       "metres above the line (the panel gives the exact height). (b) The same pair with the "
       "curvature term subtracted instead of added: the terrain falls away from the chord and the "
       "view is clear. Both panels look entirely plausible in isolation. (c) Coarse profile "
       "sampling: an 80 m barrier one cell wide falls between two of ten samples and the engine "
       "reports a clear view. (d) The same terrain as (a) at short range: every variant agrees, "
       "which is why small study areas cannot expose the defect" % f(FMETA["fig1_km"], 1),
       ancho=140)

h2("4.2 The benchmark failed silently too")
P("Every error this research made in its own instruments was silent, and none was found by "
  "inspecting results. Five test expectations written by hand were wrong, all five for the same "
  "reason. In the field study, two of the 12 validation cases initially encoded expectations that "
  "forgot the curvature term the validation existed to check. In the present benchmark, three "
  "cases were first written at 12 km, beyond the derived critical distance, where curvature alone "
  "already blocks a plane, so the feature each case claimed to test never decided the outcome. Two "
  "of the three were caught because the reference engine did not pass them. The third was passed "
  "by the reference engine and kept passing, for the wrong reason, until the mutation matrix "
  "showed the coarse-sampling defect surviving a test named after the very barrier it should have "
  "missed.")
P("That repair was itself incomplete. When the feature check of Section 3.2 was added, it found "
  "three positive cases (the %s m barrier, the %s m barrier that must block and the ground-level "
  "target behind the %s m rise) still lying beyond the critical distance and still passing on "
  "curvature alone, whatever their feature did. They were moved to %s, %s and %s km, where the "
  "feature decides. The critical distance itself had first been derived from a mid-path "
  "approximation, D²/8R = (hₒ + hₜ)/2, which is exact only for equal heights and "
  "gave %s km instead of %s km; no verdict changed, but the benchmark was right for a reason that "
  "was not quite the stated one."
  % (g(C_BAR50["altura_rasgo_m"]), g(C_BAR2["altura_rasgo_m"]), g(C_LOMA["altura_rasgo_m"]),
     f(C_BAR50["distancia_km"], 0), f(C_BAR2["distancia_km"], 0), f(C_LOMA["distancia_km"], 0),
     f(D_CRIT_V1_KM, 1), f(D_CRIT_KM, 1)))
P("The behavioural properties failed more thoroughly. The first version of the benchmark checked "
  "four relations: %s. All %s engine candidates satisfied all four, so the first-version "
  "properties detected %s of them. The reason is structural. The four are necessary conditions "
  "that any engine symmetric in the two ends of the profile and monotone in heights and distance "
  "satisfies, broken or not, and every injected defect preserves that structure. The benchmark "
  "therefore contained four tests that passed and measured nothing, which is the thesis of this "
  "paper applied to its own instruments. The current properties were designed to engage specific "
  "defects (swapping unequal heights engages a target height of zero, a single dominant cell "
  "engages coarse sampling, the derived critical distance engages both curvature defects), and "
  "each non-equivalent candidate is now killed by at least one of them (Table 3)."
  % (_lista([PRUEBA_EN[n] for n in PV1["nombres"]]), num(PV1["mutantes_evaluados"]),
     "none" if PV1["mutantes_detectados"] == 0 else num(PV1["mutantes_detectados"])))
P("One further silent failure occurred in the measurement of the production engines (Section 3.6). "
  "The first r.viewshed runs passed the refraction coefficient without the ‑r flag that "
  "activates it, and the program ignored the coefficient without a warning: its source code applies "
  "the coefficient only when the flag is set. Over a plane, the view with ‑c and the "
  "coefficient alone was lost between %s and %s km, exactly as with ‑c alone, whereas with "
  "‑c and ‑r it was lost between %s and %s km. No verdict of the benchmark changed, but "
  "the method as described was not the method run, and it was found by reading the program, not "
  "its output." % (REF_CSINR + REF_CR))
P("The episode is small and, precisely for that reason, representative: expectations and "
  "properties are code, they fail like code, and they fail silently like code. Two practices "
  "follow. Expectations should be derived from theory wherever a closed form exists and checked "
  "mechanically for the reason they pass, and the benchmark itself should be audited by mutation "
  "analysis. Between them, those two checks caught every test in this study that passed for the "
  "wrong reason.")

h2("4.3 What the design defects do to inference")
P("Table 4 and Fig. 4 give the laboratory results. The correct procedure behaves as the "
  "exchangeability argument requires. Under S0 its rejection rate is %s %% (95 %% confidence "
  "interval, CI, %s–%s %%, Wilson score interval; Wilson, 1927) at α = 0.05, and its "
  "p values are compatible with uniformity (Kolmogorov–Smirnov test, KS, asymptotic p = %s; "
  "the p values are discretised to multiples of 1/(N + 1), which makes the test slightly "
  "conservative). Under S1 its power is %s %% against a theoretical ceiling of %s %%. The "
  "laboratory, in other words, is calibrated, and that is what entitles it to measure the defects; "
  "with %d replicates, however, the interval excludes only gross miscalibration (Section 5.4)."
  % (pct(RESU["S0"]["correcto"]["rechazo"], 1),
     pct(RESU["S0"]["correcto"]["rechazo_ic95"][0], 1),
     pct(RESU["S0"]["correcto"]["rechazo_ic95"][1], 1),
     f(RESU["S0"]["correcto"]["ks_p_uniforme"], 3),
     pct(RESU["S1"]["correcto"]["rechazo"]), pct(POT_TEO), R_))

P("Letting the null sample the lake does not inflate the false-positive rate; its effect is less "
  "visible and more damaging. Null placements on a perfect plane see almost everything, the null "
  "distribution shifts upwards, and every real effect is swamped: power collapses from %s %% to "
  "%s %%, with the mean z under a true effect falling from %s to %s. This is the mechanism that "
  "erased the field study's result before the lake was masked (z = %s before, against z = %s "
  "after). A defect of this polarity is the more dangerous for being ‘conservative’: it produces "
  "no spurious discoveries to retract, only true effects that were never seen."
  % (pct(RESU["S1"]["correcto"]["rechazo"]), pct(RESU["S1"]["agua"]["rechazo"]),
     f(RESU["S1"]["correcto"]["z_media"], 2), f(RESU["S1"]["agua"]["z_media"], 2),
     fz(Z_CAMPO_AGUA), fz(Z_CAMPO_OK)))

P("The tight crop is the more troubling result of the experiment, because it hides even from the "
  "audit one would design to find it. Taken marginally across landscapes, its S0 p values are "
  "compatible with uniformity (KS p = %s) and its mean paired shift in z relative to the correct "
  "procedure is %s: the bias changes sign with the alignment between cloud and grain, and over an "
  "ensemble of landscapes it cancels. A calibration study of the defective procedure alone, at any "
  "number of replicates, would therefore pass it. The paired design exposes what the marginal one "
  "cannot. On identical data the shift has a standard deviation of %s, several times the Monte "
  "Carlo floor of Section 3.4, and its direction is not noise: it correlates with the angle "
  "between the observed cloud and the terrain grain (Spearman's ρ = %s, two-sided permutation "
  "p < 0.001; Fig. 4c)."
  % (f(RESU["S0"]["recorte"]["ks_p_uniforme"], 3), f(MEC["dz_medio"], 2), f(MEC["dz_sd"], 2),
     f(MEC["spearman_desalineacion"], 2)))
P("Clouds lying along the grain see their contrast inflated, clouds lying across it deflated, and "
  "the effects cancel only across an ensemble of landscapes that no analyst ever has: any single "
  "study sits at one point of Fig. 4c and inherits the bias of that point. The laboratory does not "
  "predict the sign the field case took (z = %s inflated to z = %s); it shows that the sign is not "
  "predictable from the procedure alone, which is precisely why the defect is silent and why D2, "
  "not a calibration study, is the right check. Under a real effect the cost is unambiguous: power "
  "falls from %s %% to %s %%."
  % (fz(Z_CAMPO_OK), fz(Z_CAMPO_RECORTE),
     pct(RESU["S1"]["correcto"]["rechazo"]), pct(RESU["S1"]["recorte"]["rechazo"])))

table("Table 4", "Calibration and power of the three procedures over %d paired replicates "
      "(N = %d null placements per contrast, one-sided, α = 0.05). Under S0 a sound procedure "
      "rejects at rate α and its p values are uniform; under S1 the theoretical power ceiling "
      "is %s %%. SD, standard deviation; KS p, p value of the Kolmogorov–Smirnov test of "
      "uniformity" % (R_, N_NULL, pct(POT_TEO)),
      ["Procedure", "S0: mean z (SD)", "S0: rejection", "S0: KS p",
       "S1: mean z (SD)", "S1: power"],
      [[nombre,
        "%s (%s)" % (f(RESU["S0"][k]["z_media"], 2), f(RESU["S0"][k]["z_sd"], 2)),
        pct(RESU["S0"][k]["rechazo"], 1) + " %",
        f(RESU["S0"][k]["ks_p_uniforme"], 3),
        "%s (%s)" % (f(RESU["S1"][k]["z_media"], 2), f(RESU["S1"][k]["z_sd"], 2)),
        pct(RESU["S1"][k]["rechazo"]) + " %"]
       for k, nombre in (("correcto", "correct"), ("agua", "water unmasked"),
                         ("recorte", "tight crop"))])

figure("fig_laboratorio.png", "Fig. 3",
       "The landscape laboratory. (a) One synthetic replicate: anisotropic terrain with a lake "
       "built by flooding a basin to a constant elevation, the observed elongated cloud (filled "
       "circles), three null placements (open circles), and the tightly cropped sampling region "
       "(dashed rectangle). (b) Diagnostic D2 on the full region: all %d orientations of the null "
       "placement fit. (c) The same diagnostic on the cropped region (solid: orientations that fit; "
       "hatched: excluded): only orientations near the cloud's own axis survive. The field study "
       "reports %d of %d for its own crop" % (CFG["pasos_orientacion"], ORIENT_CAMPO,
                                              ORIENT_TOTAL_CAMPO))

figure("fig_consecuencias.png", "Fig. 4",
       "What the defects do to inference, over %d paired replicates. (a) Under no effect (S0), the "
       "empirical cumulative distribution function (CDF) of p values: the correct procedure tracks "
       "the diagonal (uniform, as exchangeability requires); the water-unmasked procedure collapses "
       "towards p = 1; the tight crop also tracks the diagonal, so that marginally the defect is "
       "invisible, and panel (c) shows where it hides. (b) Under a real effect (S1), z by procedure "
       "(bar: mean), with the empirical power below each column and the theoretical ceiling in the "
       "panel title. (c) The paired shift in z under the crop against the misalignment between "
       "cloud and terrain grain; ρs is Spearman's rank correlation. The direction of the bias "
       "is a property of the landscape, not of the data" % R_)

h2("4.4 The diagnostics flag both defects")
P("Across all replicates, %s %% of the null placements accepted by the water-unmasked procedure "
  "included at least one site on water (diagnostic D1; the sound design scores zero by "
  "construction), and the cropped sampling region admitted on average %s %% of the %d "
  "orientations against %s %% for the full region (diagnostic D2). Neither check needs ground "
  "truth, both are computed from placements the contrast draws anyway, and either one prints a "
  "number that no analyst could accept."
  % (pct(DIAG["agua_nulos_que_pisan_media"]), pct(DIAG["cobertura_recorte_S0_media"]),
     CFG["pasos_orientacion"], pct(DIAG["cobertura_completa_media"])))

h2("4.5 Two production engines measured against the benchmark")
_rest = lambda a: "%d of %d" % (a["coinciden"], a["de"])
assert ATR_G["oz"]["coinciden"] == ATR_G["cc"]["coinciden"]
P("Table 5 gives the outcome of the runs described in Section 3.6. Configured deliberately, both "
  "engines are correct: each passes all %d cases, including the derived curvature thresholds. The "
  "geometry of these two engines is not the problem. At their shipped defaults, however, both "
  "depart from the benchmark. Left with only its mandatory arguments, gdal_viewshed answers a "
  "different question, whether the ground surface at the target is visible, because its target "
  "height defaults to zero. Its verdict differs from the benchmark expectation on %s of the %d "
  "cases, in every one by declaring blocked a target that the study places above the ground, and "
  "restoring the target height alone recovers %s cases, whereas restoring the observer height or "
  "the curvature coefficient alone leaves %s. A %s m monument behind a %s m rise disappears."
  % (N_CASOS, num(G_TV), N_CASOS, _rest(ATR_G["tz"]), _rest(ATR_G["oz"]),
     g(C_30["h_tgt"]), g(C_30["altura_rasgo_m"])))
P("The r.viewshed program fails %s cases, and in both directions. Its target height also defaults to zero, "
  "which declares blocked %s targets that are visible; and it applies no Earth-curvature "
  "correction unless the ‑c flag is passed, which declares visible %s targets that are "
  "blocked: with its shipped settings it reports a clear line of sight across %s km of flat "
  "terrain, beyond the geometric horizon. Restoring the target height alone recovers %s cases, and "
  "restoring curvature and refraction alone %s. Curvature off by default is not peculiar to GRASS: "
  "according to their documentation, the Viewshed tool of ArcGIS and the visibility plug-in of "
  "Čučković (2016) also ship with it off, and of these tools only gdal_viewshed, since GDAL 3.4, "
  "applies it unless told otherwise. In the QGIS processing dialogue for r.viewshed the curvature option is a visible "
  "check box, off by default."
  % (num(R_TV + R_VT), num(R_TV), num(R_VT), f(C40["distancia_km"], 0),
     _rest(ATR_R["target_elevation"]), _rest(ATR_R["curvatura_y_refraccion"])))
P("Put side by side, the two engines at their shipped defaults disagree on %s of the %d cases and "
  "agree on %d. The disagreements all occur over a plane, where one engine applies curvature and "
  "the other does not: gdal_viewshed is right on %s of them and r.viewshed on %s, the latter only "
  "because its two defaults cancel (a target on the ground, which curvature would hide, on an Earth "
  "without curvature). Of the %d cases on which they agree, %s share the same wrong verdict: in "
  "each, the target stands on the ground by default and a low barrier or a rise hides it in both "
  "programs. Agreement between the two programs would thus have certified %s wrong verdicts, and "
  "disagreement would have flagged %s cases without saying which program was right."
  % (num(N_DISC), N_CASOS, N_ACUERDO, num(DISC["acierta_gdal"]), num(DISC["acierta_grass"]),
     N_ACUERDO, num(N_COMPARTIDO), num(N_COMPARTIDO), num(N_DISC)))
P("The consequence is the quantity Fisher (1993) described but could not attribute. Two engines "
  "that are each correct can return contradictory verdicts on identical terrain, or the same wrong "
  "verdict, depending on defaults that nothing in either output reports. Comparing implementations "
  "with one another, which is how inter-implementation uncertainty has usually been approached, "
  "cannot separate these situations; only cases whose answer is derived independently of any "
  "implementation can. This is why a benchmark is the right instrument: it is the only one of the "
  "controls considered here that distinguishes a correct engine from a correct engine badly "
  "configured, and it turns the inter-implementation disagreement of Section 2.1 from a property "
  "of the operation into a list of attributable causes.")


def _atr(atr, nombres):
    return "; ".join("%s: %s" % (n, frac(atr[k]["coinciden"], atr[k]["de"])) for k, n in nombres)


table("Table 5",
      "Two production viewshed engines against the %d benchmark cases, configured with the "
      "parameters of this study and at their shipped defaults (mandatory arguments only). The last "
      "column gives the cases passed when a single shipped default is restored to the study's "
      "value. At shipped defaults the two engines disagree on %d cases, return the same wrong "
      "verdict on %d and are both right on %d" % (N_CASOS, N_DISC, N_COMPARTIDO, N_AMBOS_BIEN),
      ["Engine", "Configured", "Shipped defaults", "Visible declared blocked",
       "Blocked declared visible", "One default restored"],
      [["gdal_viewshed (GDAL %s)" % _G["version_gdal"], _G["correcto"], _G["de_fabrica"],
        G_TV, G_VT,
        _atr(ATR_G, (("tz", "target"), ("oz", "observer"), ("cc", "curvature")))],
       ["r.viewshed (GRASS %s)" % _R["version"], _R["correcto"], _R["de_fabrica"], R_TV, R_VT,
        _atr(ATR_R, (("target_elevation", "target"), ("observer_elevation", "observer"),
                     ("curvatura_y_refraccion", "curvature and refraction")))]],
      widths=[34, 20, 20, 22, 22, 42])

# ================================================================== discussion
h1("5 Discussion")
h2("5.1 Six practices")
P("The instruments presented here are inexpensive, and the failures they target are not "
  "hypothetical: all three field-documented defects pass silently through review and "
  "reproduction, and two of them each suffice, on their own, to decide the conclusion of a study. "
  "Six practices follow from the results, in rising order of novelty for the discipline.")
P("First, validate the geometric engine against synthetic terrains of known answer before it "
  "touches real terrain; on real terrain there is nothing to validate against (Fisher, 1993). "
  "Second, derive test expectations from theory wherever a closed form exists, and check "
  "mechanically that each test passes for the reason it claims; Section 4.2 shows handwritten "
  "expectations and properties failing silently in ways no one would tolerate in the code under "
  "test. Third, audit the benchmark itself by mutation analysis, distinguishing equivalent mutants "
  "from holes; it is the instrument that caught, here, four properties that measured nothing.")
P("Fourth, record and justify every parameter handed to a production engine, and do not take "
  "agreement between two programs as validation: Section 4.5 shows two engines that each pass the "
  "whole benchmark returning the same wrong verdict on %s of its cases, and contradictory verdicts "
  "on %s others, when both are left at their own defaults. Fifth, diagnose the sampler of the null "
  "model directly: placement validity (D1) and orientation coverage (D2) would have caught both "
  "design defects at the cost of two printed numbers. Sixth, publish the defective runs alongside "
  "the corrected analysis, as the field study did: a claim that a defect ‘would have changed the "
  "result’ is itself a computational claim, and it deserves the same verifiability as the result."
  % (num(N_COMPARTIDO), num(N_DISC)))

h2("5.2 Reproducibility, replicability and validity")
P("None of this competes with the reproducibility agenda; it completes it. Marwick's (2017) "
  "programme makes an analysis repeatable by others, and that is the precondition for everything "
  "here: a benchmark of the kind this paper publishes is only auditable because it ships as "
  "runnable code, and the two production engines could only be measured because they are open "
  "source (Ducke, 2012). The two guarantees must nonetheless not be confused. Reproducibility "
  "certifies the transport of a computation; validation certifies its content. The field episode "
  "behind this paper was fully reproducible at every moment during which it was wrong.")
P("The taxonomy that Kedron et al. (2021) take from the National Academies of Sciences, "
  "Engineering, and Medicine (2019) makes the point precise. Reproducibility asks whether the same "
  "data and code return the same result; replicability asks whether new data return the same "
  "finding. A silent failure of the engine survives both, because the defective procedure travels "
  "with the study: a second team re-running the deposited code reproduces the inverted sign, and a "
  "second team applying the same shipped default to a new landscape replicates the same wrong "
  "verdicts. What the two guarantees leave uncovered is the correspondence between the procedure "
  "and the quantity it claims to compute, and that correspondence can only be established against "
  "cases where the answer is known independently of the procedure. That is what a benchmark with "
  "derived expectations provides, and what real terrain, by its nature, cannot.")
P("This is the oracle problem of Section 2.2 stated in the vocabulary of open science, and the "
  "answer is the same: the discipline's methodological literature should publish benchmarks "
  "alongside methods, so that a new engine, a new plug-in or a new default can be measured rather "
  "than trusted. There is also a theoretical corollary for how methods are argued in archaeology. "
  "Much of the visibility literature reviewed in Section 2.1 responds to uncertainty by modelling "
  "it (fuzzy viewsheds, probabilistic visibility, network models that are robust to individual "
  "edges), and that response is right for the uncertainty that comes from the data. It is the "
  "wrong response for the uncertainty that comes from defects, because a defect is not a "
  "distribution to be propagated but a mistake to be found, and propagating it only lends it the "
  "authority of an error bar. The two kinds of uncertainty demand different instruments, and the "
  "literature reviewed here has so far concentrated on the first.")

h2("5.3 Implications for visibility studies")
P("For the practising analyst the results reduce to a short list of parameters that a visibility "
  "paper should report and currently rarely does. Table 6 lists them, with the values that two "
  "widely used engines ship with: the engine, its version and its algorithm; whether curvature and "
  "refraction were applied and with what coefficient, since Section 4.5 shows that the answer "
  "differs between two tools installed side by side; the observer and target heights, since a "
  "target height of zero, the shipped default of both engines, asks whether the ground is visible "
  "rather than whether a monument is (Ogburn, 2006); the elevation model and its treatment of "
  "water; the sampling region of the null model together with diagnostics D1 and D2; and the "
  "evidence that the engine passes a benchmark of known answers. Kormann and Lock (2014) showed "
  "that curvature and refraction change results at archaeological ranges; this paper shows that "
  "whether they are applied at all can depend on a flag that is off by default and that the "
  "analyst must know to look for.")
P("The plug-in of Čučković (2016), which implements its own line-of-sight engine, and the network "
  "methods of Brughmans et al. (2015) rest on lines of sight that have not been measured against a "
  "benchmark of derived answers; the one deposited here is an instrument with which they can be. "
  "The results also bear on how the field's null models are designed. Lake and Woodman (2003) and "
  "Wheatley and Gillings (2000) settled which comparison a visibility study should make; the "
  "laboratory shows that even the right comparison fails silently if the null is allowed to sample "
  "where no site could stand, or is denied orientations that the real configuration could have "
  "taken. Both are properties of the sampler, not of the null model as a concept, and both are "
  "checkable before any line of sight is computed.")


def _km_o_ninguna(v):
    return "none" if v in (-1, "sin limite") else "%s m" % g(v)


table("Table 6", "Parameters that every visibility study should declare, with the shipped defaults "
      "of the two production engines measured (documented defaults of the versions in Table 5; "
      "‘n/a’, not an engine setting)",
      ["Parameter", "Why it matters", "gdal_viewshed", "r.viewshed"],
      [["Engine, version, algorithm", "implementations disagree (Sections 2.1, 4.5)",
        "GDAL %s" % _G["version_gdal"], "GRASS %s" % _R["version"]],
       ["Earth curvature", "severs views beyond a few kilometres (Section 3.2)",
        "on (‑cc %s)" % g(GD["cc"]), "off unless ‑c"],
       ["Refraction coefficient k", "moves the critical distance",
        "1 − cc = %s" % f(1 - GD["cc"], 3), "%s, used only with ‑r" % f(RD["refraction_coeff"], 3)],
       ["Observer height", "lifts every line of sight", "%s m" % g(GD["oz"]),
        "%s m" % g(RD["observer_elevation"])],
       ["Target height", "zero asks whether the ground is visible (Section 4.5)",
        "%s m" % g(GD["tz"]), "%s m" % g(RD["target_elevation"])],
       ["Maximum distance", "truncates long views", _km_o_ninguna(GD["md"]),
        _km_o_ninguna(RD["max_distance"])],
       ["Elevation model", "source, resolution and vertical datum", "input", "input"],
       ["Water and nodata", "a flat lake feeds the null (Section 4.3)", "n/a", "n/a"],
       ["Null sampling region", "a tight crop biases the contrast (Section 4.3)", "n/a", "n/a"],
       ["Diagnostics D1 and D2", "must read 0 and 100 % (Section 3.5)", "n/a", "n/a"],
       ["Benchmark result", "configured; at shipped defaults (Section 4.5)",
        "%s; %s" % (_G["correcto"], _G["de_fabrica"]), "%s; %s" % (_R["correcto"], _R["de_fabrica"])]],
      widths=[36, 64, 30, 30])

h2("5.4 Limitations")
P("The benchmark validates one algorithmic family, Boolean line of sight over a sampled profile "
  "with the effective-radius correction, and it does so on profiles that run along one row of the "
  "grid: observer and target share a row, and every case is in effect one-dimensional. How an "
  "oblique ray is sampled or interpolated, which is where many of the differences between "
  "implementations arise (Fisher, 1993; Riggs & Dean, 2007), is not exercised, and algorithms that "
  "do not trace each line of sight separately are not stressed; a %s on these cases says nothing "
  "about behaviour off the grid axes. Probabilistic and fuzzy viewsheds, and implementations with "
  "sub-cell interpolation, need their own cases, though the properties transfer unchanged. There "
  "is no elevation error and no vegetation, and the lake is an exact plane."
  % _G["correcto"])
P("The laboratory uses one statistic (the density of the complete intervisibility network), one "
  "cloud shape of %d sites, one null model and one-sided contrasts with N = %d null placements, "
  "and it does not cross engine defects with design defects. With %d replicates, calibration is "
  "verified only coarsely: the 95 %% CI of the correct procedure's rejection rate reaches %s %%. "
  "Its landscapes are stylised; they are built to make the mechanisms of the defects measurable, "
  "not to imitate any particular geography, and the laboratory's exactness holds for its own "
  "constructed scenarios. The p value of a real study does not inherit it, because real sites are "
  "not placed by the rules of the null model. What transfers to the field is the measured "
  "behaviour of procedures, not of sites."
  % (CFG["n_sitios"], N_NULL, R_, pct(RESU["S0"]["correcto"]["rechazo_ic95"][1], 1)))
P("The defect list is not a census. The three documented defects come from a single episode of a "
  "single team; the engine defaults were measured in one version of each program and only through "
  "their command-line interfaces; and defaults change between releases. The benchmark and the "
  "mutation harness are deposited so that the measurement can be repeated and the list can grow. "
  "Finally, D2 = 100 % may be legitimately unattainable when the study area is small or irregular "
  "relative to the site configuration. D2 should then be reported rather than forced: the null is "
  "restricted to the orientations that fit, the coverage obtained is stated, and the contrast is "
  "read as conditional on it.")

h2("5.5 Future work")
P("The natural extension is horizontal: the same defect-injection methodology applies wherever "
  "archaeology computes on rasters (least-cost paths, hydrological modelling, predictive "
  "modelling), and each domain has its own silent defaults awaiting a benchmark. A second "
  "extension is comparative and geometric: Section 4.5 measured two engines on profiles aligned "
  "with the grid, and the same harness, extended to oblique profiles, can be pointed at other "
  "published viewshed implementations, turning Fisher's (1993) observation of "
  "inter-implementation disagreement into a standing, attributable measurement that is updated "
  "with each release.")

# ================================================================= conclusions
h1("6 Conclusions")
P("A reproducible analysis reproduces its errors. This paper has shown, for archaeological "
  "visibility analysis, that there is a class of defects that raise no error, return plausible "
  "output, survive both review and re-execution, and decide the conclusion of the study that "
  "contains them. Three were documented in the field; six are reproduced here, and a seventh "
  "candidate proved harmless. Against them the paper offers a benchmark whose expectations are "
  "derived and whose adequacy is measured, a measurement that caught the benchmark's own first "
  "properties testing nothing, a laboratory in which the truth is known by construction, two "
  "diagnostics that cost almost nothing, and the finding that two widely used, freely available "
  "engines are correct when configured and, at their defaults, wrong in ways that comparing them "
  "with each other would not reveal. The practices that follow are inexpensive and the code that "
  "implements them is deposited. What they add to the reproducibility programme is the one "
  "guarantee that programme cannot give: that what is being reproduced is right.")

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
  "(Mamani Calisaya, 2026) at https://doi.org/%s (concept identifier, resolving to the latest "
  "version). The field study whose defects are reproduced here is likewise openly deposited, "
  "including its pre-correction runs (Mamani Calisaya et al., 2026), at https://doi.org/%s."
  % (DOI_ESTE, DOI_CASO), after=8, align=WD_ALIGN_PARAGRAPH.LEFT)

etiqueta("Author contributions", after=3)
P("%s: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, "
  "Data curation, Writing – original draft, Writing – review and editing, Visualization "
  "(CRediT taxonomy)." % AUTOR, after=10)

# ================================================================== references
# Los tramos entre asteriscos van en cursiva (APA 7: revista y volumen; titulo de
# libro, actas, programa o deposito). Los asteriscos no llegan al .docx.
etiqueta("References", after=6)
REFERENCES = [
    "Baker, M. (2016). 1,500 scientists lift the lid on reproducibility. *Nature, 533*(7604), "
    "452–454. https://doi.org/10.1038/533452a",
    "Brughmans, T., & Brandes, U. (2017). Visibility network patterns and methods for studying "
    "visual relational phenomena in archeology. *Frontiers in Digital Humanities, 4*, Article 17. "
    "https://doi.org/10.3389/fdigh.2017.00017",
    "Brughmans, T., Keay, S., & Earl, G. (2015). Understanding inter-settlement visibility in Iron "
    "Age and Roman southern Spain with exponential random graph models for visibility networks. "
    "*Journal of Archaeological Method and Theory, 22*(1), 58–143. "
    "https://doi.org/10.1007/s10816-014-9231-x",
    "Brunsdon, C. (2016). Quantitative methods I: Reproducible research and quantitative geography. "
    "*Progress in Human Geography, 40*(5), 687–696. https://doi.org/10.1177/0309132515599625",
    "Chen, T. Y., Kuo, F.-C., Liu, H., Poon, P.-L., Towey, D., Tse, T. H., & Zhou, Z. Q. (2018). "
    "Metamorphic testing: A review of challenges and opportunities. *ACM Computing Surveys, 51*(1), "
    "Article 4. https://doi.org/10.1145/3143561",
    "Claessen, K., & Hughes, J. (2000). QuickCheck: A lightweight tool for random testing of Haskell "
    "programs. In *Proceedings of the Fifth ACM SIGPLAN International Conference on Functional "
    "Programming (ICFP '00)* (pp. 268–279). ACM. https://doi.org/10.1145/351240.351266",
    "Čučković, Z. (2016). Advanced viewshed analysis: A Quantum GIS plug-in for the analysis of "
    "visual landscapes. *The Journal of Open Source Software, 1*(4), Article 32. "
    "https://doi.org/10.21105/joss.00032",
    "DeMillo, R. A., Lipton, R. J., & Sayward, F. G. (1978). Hints on test data selection: Help for "
    "the practicing programmer. *Computer, 11*(4), 34–41. https://doi.org/10.1109/C-M.1978.218136",
    "Ducke, B. (2012). Natives of a connected world: Free and open source software in archaeology. "
    "*World Archaeology, 44*(4), 571–579. https://doi.org/10.1080/00438243.2012.743259",
    "Eklund, A., Nichols, T. E., & Knutsson, H. (2016). Cluster failure: Why fMRI inferences for "
    "spatial extent have inflated false-positive rates. *Proceedings of the National Academy of "
    "Sciences, 113*(28), 7900–7905. https://doi.org/10.1073/pnas.1602413113",
    "Fisher, P. F. (1993). Algorithm and implementation uncertainty in viewshed analysis. "
    "*International Journal of Geographical Information Systems, 7*(4), 331–347. "
    "https://doi.org/10.1080/02693799308901965",
    "Fisher, P. F. (1995). An exploration of probable viewsheds in landscape planning. "
    "*Environment and Planning B: Planning and Design, 22*(5), 527–546. "
    "https://doi.org/10.1068/b220527",
    "GDAL/OGR contributors. (2026). *GDAL* (Version %s) [Computer software]. Zenodo. " % _G["version_gdal"] +
    
    "https://doi.org/10.5281/zenodo.20700933",
    "Gillings, M. (2015). Mapping invisibility: GIS approaches to the analysis of hiding and "
    "seclusion. *Journal of Archaeological Science, 62*, 1–14. "
    "https://doi.org/10.1016/j.jas.2015.06.015",
    "Gillings, M. (2017). Mapping liminality: Critical frameworks for the GIS-based modelling of "
    "visibility. *Journal of Archaeological Science, 84*, 121–128. "
    "https://doi.org/10.1016/j.jas.2017.05.004",
    "GRASS Development Team. (2026). *GRASS* (Version %s) [Computer software]. Zenodo. " % _R["version"] +
    
    "https://doi.org/10.5281/zenodo.20083515",
    "Hatton, L. (1997). The T experiments: Errors in scientific software. *IEEE Computational "
    "Science and Engineering, 4*(2), 27–38. https://doi.org/10.1109/99.609829",
    "Hatton, L., & Roberts, A. (1994). How accurate is scientific software? *IEEE Transactions on "
    "Software Engineering, 20*(10), 785–797. https://doi.org/10.1109/32.328993",
    "Haverkort, H., Toma, L., & Zhuang, Y. (2009). Computing visibility on terrains in external "
    "memory. *ACM Journal of Experimental Algorithmics, 13*, Article 1.5. "
    "https://doi.org/10.1145/1412228.1412233",
    "Herndon, T., Ash, M., & Pollin, R. (2014). Does high public debt consistently stifle economic "
    "growth? A critique of Reinhart and Rogoff. *Cambridge Journal of Economics, 38*(2), 257–279. "
    "https://doi.org/10.1093/cje/bet075",
    "Hook, D., & Kelly, D. (2009). Testing for trustworthiness in scientific software. In *2009 "
    "ICSE Workshop on Software Engineering for Computational Science and Engineering* (pp. 59–64). "
    "IEEE. https://doi.org/10.1109/SECSE.2009.5069163",
    "Ivie, P., & Thain, D. (2018). Reproducibility in scientific computing. *ACM Computing Surveys, "
    "51*(3), Article 63. https://doi.org/10.1145/3186266",
    "Jia, Y., & Harman, M. (2011). An analysis and survey of the development of mutation testing. "
    "*IEEE Transactions on Software Engineering, 37*(5), 649–678. "
    "https://doi.org/10.1109/TSE.2010.62",
    "Kanewala, U., & Bieman, J. M. (2014). Testing scientific software: A systematic literature "
    "review. *Information and Software Technology, 56*(10), 1219–1232. "
    "https://doi.org/10.1016/j.infsof.2014.05.006",
    "Kedron, P., Li, W., Fotheringham, S., & Goodchild, M. (2021). Reproducibility and "
    "replicability: Opportunities and challenges for geospatial research. *International Journal "
    "of Geographical Information Science, 35*(3), 427–445. "
    "https://doi.org/10.1080/13658816.2020.1802032",
    "Kormann, M., & Lock, G. (2014). Exploring the effects of curvature and refraction on "
    "GIS-based visibility studies. In G. Earl, T. Sly, A. Chrysanthi, P. Murrieta-Flores, C. "
    "Papadopoulos, I. Romanowska, & D. Wheatley (Eds.), *Archaeology in the digital era: Papers "
    "from the 40th Annual Conference of Computer Applications and Quantitative Methods in "
    "Archaeology (CAA), Southampton, 26–29 March 2012* (pp. 428–437). Amsterdam University Press. "
    "https://doi.org/10.1515/9789048519590-046",
    "Lake, M. W., & Woodman, P. E. (2003). Visibility studies in archaeology: A review and case "
    "study. *Environment and Planning B: Planning and Design, 30*(5), 689–707. "
    "https://doi.org/10.1068/b29122",
    "Lake, M. W., Woodman, P. E., & Mithen, S. J. (1998). Tailoring GIS software for "
    "archaeological applications: An example concerning viewshed analysis. *Journal of "
    "Archaeological Science, 25*(1), 27–38. https://doi.org/10.1006/jasc.1997.0197",
    "Leek, J. T., & Peng, R. D. (2015). Reproducible research can still be wrong: Adopting a "
    "prevention approach. *Proceedings of the National Academy of Sciences, 112*(6), 1645–1646. "
    "https://doi.org/10.1073/pnas.1421412111",
    "Llobera, M. (2003). Extending GIS-based visual analysis: The concept of visualscapes. "
    "*International Journal of Geographical Information Science, 17*(1), 25–48. "
    "https://doi.org/10.1080/713811741",
    "Mamani Calisaya, M. V. (2026). *Reproducible and wrong: Silent failures in archaeological "
    "visibility analysis and a benchmark to catch them — code, benchmark and landscape laboratory* "
    "[Computer software and data set]. Zenodo. https://doi.org/10.5281/zenodo.22242923",
    "Mamani Calisaya, M. V., Mamani Calisaya, D. N., Alanoca Arocutipa, V., & Alanoca Laura, S. L. "
    "(2026). *Intervisibilidad de sitios arqueológicos en la cuenca del Titicaca: Código, datos "
    "derivados y contraejemplos* [Intervisibility of archaeological sites in the Titicaca basin: "
    "Code, derived data and counterexamples] (Version 1.3.0) [Computer software and data set]. "
    "Zenodo. https://doi.org/10.5281/zenodo.23083731",
    "Marwick, B. (2017). Computational reproducibility in archaeological research: Basic principles "
    "and a case study of their implementation. *Journal of Archaeological Method and Theory, "
    "24*(2), 424–450. https://doi.org/10.1007/s10816-015-9272-9",
    "Merali, Z. (2010). Computational science: ...Error. *Nature, 467*(7317), 775–777. "
    "https://doi.org/10.1038/467775a",
    "Miller, G. (2006). A scientist's nightmare: Software problem leads to five retractions. "
    "*Science, 314*(5807), 1856–1857. https://doi.org/10.1126/science.314.5807.1856",
    "Nackaerts, K., Govers, G., & Van Orshoven, J. (1999). Accuracy assessment of probabilistic "
    "visibilities. *International Journal of Geographical Information Science, 13*(7), 709–721. "
    "https://doi.org/10.1080/136588199241076",
    "National Academies of Sciences, Engineering, and Medicine. (2019). *Reproducibility and "
    "replicability in science*. National Academies Press. https://doi.org/10.17226/25303",
    "Nüst, D., & Pebesma, E. (2021). Practical reproducibility in geography and geosciences. "
    "*Annals of the American Association of Geographers, 111*(5), 1300–1310. "
    "https://doi.org/10.1080/24694452.2020.1806028",
    "Ogburn, D. E. (2006). Assessing the level of visibility of cultural objects in past "
    "landscapes. *Journal of Archaeological Science, 33*(3), 405–413. "
    "https://doi.org/10.1016/j.jas.2005.08.005",
    "Peng, R. D. (2011). Reproducible research in computational science. *Science, 334*(6060), "
    "1226–1227. https://doi.org/10.1126/science.1213847",
    "Phipson, B., & Smyth, G. K. (2010). Permutation p-values should never be zero: Calculating "
    "exact p-values when permutations are randomly drawn. *Statistical Applications in Genetics "
    "and Molecular Biology, 9*(1), Article 39. https://doi.org/10.2202/1544-6115.1585",
    "Riggs, P. D., & Dean, D. J. (2007). An investigation into the causes of errors and "
    "inconsistencies in predicted viewsheds. *Transactions in GIS, 11*(2), 175–196. "
    "https://doi.org/10.1111/j.1467-9671.2007.01040.x",
    "Sandve, G. K., Nekrutenko, A., Taylor, J., & Hovig, E. (2013). Ten simple rules for "
    "reproducible computational research. *PLoS Computational Biology, 9*(10), Article e1003285. "
    "https://doi.org/10.1371/journal.pcbi.1003285",
    "Schmidt, S. C., & Marwick, B. (2020). Tool-driven revolutions in archaeological science. "
    "*Journal of Computer Applications in Archaeology, 3*(1), 18–32. https://doi.org/10.5334/jcaa.29",
    "Segura, S., Fraser, G., Sanchez, A. B., & Ruiz-Cortés, A. (2016). A survey on metamorphic "
    "testing. *IEEE Transactions on Software Engineering, 42*(9), 805–824. "
    "https://doi.org/10.1109/TSE.2016.2532875",
    "Soergel, D. A. W. (2015). Rampant software errors may undermine scientific results. "
    "*F1000Research, 3*, Article 303. https://doi.org/10.12688/f1000research.5930.2",
    "Stodden, V., Seiler, J., & Ma, Z. (2018). An empirical analysis of journal policy "
    "effectiveness for computational reproducibility. *Proceedings of the National Academy of "
    "Sciences, 115*(11), 2584–2589. https://doi.org/10.1073/pnas.1708290115",
    "Wheatley, D., & Gillings, M. (2000). Vision, perception and GIS: Developing enriched "
    "approaches to the study of archaeological visibility. In G. Lock (Ed.), *Beyond the map: "
    "Archaeology and spatial technologies* (pp. 1–27). IOS Press.",
    "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. "
    "*Journal of the American Statistical Association, 22*(158), 209–212. "
    "https://doi.org/10.1080/01621459.1927.10502953",
]


def P_ref(t, size=9, after=4):
    """Entrada de referencia: sangria francesa, sin justificar, tramos *...* en cursiva."""
    assert t.count("*") % 2 == 0, "asterisco sin cerrar en: " + t[:50]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.6)
    p.paragraph_format.keep_together = True
    for i, seg in enumerate(t.split("*")):
        if seg:
            run(p, seg, size, italic=(i % 2 == 1))
    return p


for ref in REFERENCES:
    P_ref(ref)

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
i_ini = ps_.index("1 Introduction")
i_dec = ps_.index("Statements and Declarations")
cuerpo = sum(len(t.split()) for t in ps_[i_ini:i_dec])
cuerpo_tablas = sum(len(c.text.split()) for t in doc.tables for row in t.rows for c in row.cells)
largos = [(len(t.split()), t[:50]) for t in ps_[i_ini:i_dec] if len(t.split()) > 175]
print("Manuscrito ->", OUT)
print("metadatos con contenido:", docmeta.informe(OUT) or "ninguno")
print("palabras: %d en total | %d en el cuerpo (Introduction a Declarations, sin tablas) + %d en "
      "tablas | resumen: %d | figuras: %d | tablas: %d | referencias: %d"
      % (palabras, cuerpo, cuerpo_tablas, len(ABSTRACT.split()), len(doc.inline_shapes),
         len(doc.tables), len(REFERENCES)))
if largos:
    print("parrafos de mas de 175 palabras:", largos)
