# -*- coding: utf-8 -*-
"""
Auditoria del manuscrito: formato, figuras, coherencia numerica y prosa.

La misma disciplina del caso de estudio, aplicada a este articulo. Cada cifra
del texto que procede de un calculo se coteja contra el JSON correspondiente;
las figuras deben existir, estar incrustadas y estar citadas; las referencias
listadas deben estar citadas y las citadas, listadas; el ingles debe ser
britanico de forma consistente; y las propiedades del fichero no deben delatar
ni autores ni generador, porque la revision es ciega.

Salida: results/auditoria.json
"""
import json
import math
import os
import re
import sys
import zipfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from los_engine import R_EFF

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
FIG = os.path.join(RES, "figuras")
DOCX = os.path.join(BASE, "manuscript_silent_failures.docx")

ok_n, fail_n = 0, 0
items = []


def check(bloque, etiqueta, cond, detalle=""):
    global ok_n, fail_n
    if cond:
        ok_n += 1
    else:
        fail_n += 1
    items.append({"bloque": bloque, "check": etiqueta, "ok": bool(cond), "detalle": detalle})
    print("  %-5s %-58s %s" % ("OK" if cond else "FALLA", etiqueta, detalle), flush=True)


def f(x, dec=2):
    return ("%%.%df" % dec) % x


def pct(x, dec=0):
    return ("%%.%df" % dec) % (100.0 * x)


def main():
    doc = Document(DOCX)
    ps = [p.text for p in doc.paragraphs]
    texto = "\n".join(ps)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                texto += "\n" + c.text

    BEN = json.load(open(os.path.join(RES, "benchmark.json"), encoding="utf-8"))
    CAL = json.load(open(os.path.join(RES, "calibracion.json"), encoding="utf-8"))
    FMETA = json.load(open(os.path.join(FIG, "meta.json"), encoding="utf-8"))
    CT = os.path.join(BASE, "data", "caso_titicaca")

    print("AUDITORÍA DEL MANUSCRITO\n")

    # ---------------------------------------------------------------- formato
    print("1. FORMATO Y ANONIMATO")
    runs = [r for p in doc.paragraphs for r in p.runs if r.text.strip()]
    fuentes = {r.font.name for r in runs}
    check("formato", "fuente única Arial", fuentes <= {"Arial"},
          "fuentes %s" % sorted(x for x in fuentes if x))

    sec = doc.sections[0]
    check("formato", "página A4 con márgenes de 2.5 cm",
          abs(sec.page_width - 7560000) < 40000 and abs(sec.top_margin / 360000 - 2.5) < 0.05,
          "%.1f x %.1f cm" % (sec.page_width / 360000, sec.page_height / 360000))

    cuerpo = [p for p in doc.paragraphs
              if len(p.text.split()) > 25
              and not re.match(r"^(Figure|Table)\s+\d+\.", p.text.strip())]
    just = sum(1 for p in cuerpo if p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY)
    check("formato", "texto corrido justificado", just == len(cuerpo),
          "%d de %d" % (just, len(cuerpo)))

    # JAS revisa en anonimo simple y no admite portada aparte: la autoria debe
    # estar en el manuscrito, completa (nombre, filiacion, correspondencia, ORCID).
    presentes = [w for w in ("Mamani Calisaya", "Universidad Nacional del Altiplano",
                             "mmamanic@unap.edu.pe", "ORCID") if w in texto]
    check("formato", "bloque de autoría completo (anónimo simple)",
          len(presentes) == 4, "presentes: %d de 4" % len(presentes))

    corchetes = [p for p in ps if p.strip().startswith("[") and p.strip().endswith("]")]
    check("formato", "sin marcadores de posición entre corchetes", not corchetes,
          corchetes[0][:50] if corchetes else "")

    # ---------------------------------------------------------------- figuras
    print("\n2. FIGURAS")
    from PIL import Image
    for fn in ("fig_pipeline.png", "fig_anatomia.png", "fig_laboratorio.png",
               "fig_consecuencias.png"):
        p = os.path.join(FIG, fn)
        if not os.path.exists(p):
            check("figuras", fn, False, "no existe")
            continue
        im = Image.open(p)
        dpi = im.info.get("dpi", (0, 0))[0]
        check("figuras", "%s: resolución" % fn, dpi >= 299 and im.width >= 1800,
              "%dx%d px, %d dpi" % (im.width, im.height, dpi))
    check("figuras", "cuatro figuras incrustadas", len(doc.inline_shapes) == 4,
          "%d" % len(doc.inline_shapes))
    cuerpo_txt = "\n".join(p for p in ps if not re.match(r"^Figure\s+\d+\.\s", p.strip()))
    for i in (1, 2, 3, 4):
        check("figuras", "Figure %d citada en el texto" % i,
              ("Figure %d" % i) in cuerpo_txt or ("Figure %dc" % i) in cuerpo_txt)
    n_capt = len([p for p in ps if re.match(r"^Figure\s+\d+\.", p.strip())])
    check("figuras", "cuatro pies de figura", n_capt == 4, "%d" % n_capt)
    # se excluyen los pies («Table N. …»), no las frases que citan («Table 3 and …»)
    cuerpo_tab = "\n".join(p for p in ps if not re.match(r"^Table\s+\d+\.\s", p.strip()))
    for i in (1, 2, 3):
        check("figuras", "Table %d citada en el texto" % i, ("Table %d" % i) in cuerpo_tab)

    # ------------------------------------------------------------- coherencia
    print("\n3. COHERENCIA NUMÉRICA")
    N_TESTS = BEN["motor_correcto"]["pruebas"]
    N_CASOS = len(BEN["motor_correcto"]["casos"])
    N_PROPS = len(BEN["motor_correcto"]["propiedades"])
    check("números", "total de pruebas del banco", ("all %d tests" % N_TESTS) in texto,
          "%d" % N_TESTS)
    check("números", "casos y propiedades",
          ("%d terrain cases" % N_CASOS) in texto and
          ("%d behavioural properties" % N_PROPS) in texto,
          "%d + %d" % (N_CASOS, N_PROPS))

    d_crit = math.sqrt(8.0 * R_EFF * (1.7 + 3.0) / 2.0) / 1000.0
    check("números", "distancia crítica derivada", ("%s km" % f(d_crit, 1)) in texto,
          "%s km" % f(d_crit, 1))

    n_comp = BEN["mutantes"]["extremos_incluidos"]["comparaciones_equivalencia"]
    check("números", "comparaciones del barrido de equivalencia",
          ("{:,}".format(n_comp)) in texto, "{:,}".format(n_comp))

    for d, v in BEN["mutantes"].items():
        esperado = "%d / %d" % (v["pruebas_que_saltan"], N_TESTS)
        check("números", "matriz de mutantes: %s" % d, esperado in texto, esperado)

    RESU = CAL["resumen"]
    for esc in ("S0", "S1"):
        for proc in ("correcto", "agua", "recorte"):
            c = RESU[esc][proc]
            par = "%s (%s)" % (f(c["z_media"], 2), f(c["z_sd"], 2))
            check("números", "tabla 3: z de %s/%s" % (esc, proc), par in texto, par)
    check("números", "potencia teórica",
          ("%s %%" % pct(RESU["potencia_teorica_S1_correcto"])) in texto,
          pct(RESU["potencia_teorica_S1_correcto"]) + " %")
    m = RESU["mecanismo_recorte"]
    check("números", "rho de Spearman del mecanismo",
          f(m["spearman_desalineacion"], 2) in texto, f(m["spearman_desalineacion"], 2))
    dgn = RESU["diagnosticos"]
    check("números", "cobertura del recorte (D2)",
          ("%s %%" % pct(dgn["cobertura_recorte_S0_media"])) in texto,
          pct(dgn["cobertura_recorte_S0_media"]) + " %")

    # las z del caso de campo, contra los ficheros del deposito copiados
    def cz(fn):
        return json.load(open(os.path.join(CT, fn), encoding="utf-8"))["por_alcance"]["5000"]["z"]

    for fn, eti in (("nulo_rigido.json", "z corregida del caso de campo"),
                    ("nulo_rigido_sin_mascara.json", "z del agua sin enmascarar"),
                    ("nulo_rigido_n300.json", "z del recorte del caso de campo")):
        v = "%+.2f" % cz(fn)
        # el texto usa el signo menos tipografico
        check("números", eti, v in texto or v.replace("-", "−") in texto, v)

    check("números", "distancia de la figura 1",
          ("%s km" % f(FMETA["fig1_km"], 1)) in texto, "%s km" % f(FMETA["fig1_km"], 1))
    check("números", "réplicas y nulos del laboratorio",
          ("%d replicates" % CAL["config"]["replicas"]) in texto
          and ("%d null placements" % CAL["config"]["n_null"]) in texto,
          "%d, %d" % (CAL["config"]["replicas"], CAL["config"]["n_null"]))

    # -------------------------------------------------------------------- prosa
    print("\n4. PROSA Y APARATO CRÍTICO")
    partes = texto.split("References")
    cuerpo_ref, lista_ref = partes[0], partes[-1]
    sin_citar = []
    for linea in lista_ref.split("\n"):
        mm = re.match(r"^([A-Z][\w'áéíóú-]+),", linea.strip())
        if mm and mm.group(1) not in cuerpo_ref:
            sin_citar.append(mm.group(1))
    check("prosa", "toda referencia listada está citada", not sin_citar,
          "sin citar: %s" % sin_citar if sin_citar else
          "%d referencias" % len([l for l in lista_ref.split(chr(10))
                                  if re.match(r"^[A-Z][\w'-]+,", l.strip())]))

    # ingles britanico consistente, fuera de las referencias (los titulos ajenos
    # conservan su grafia original)
    americanismos = [w for w in ("artifact", "behavior", "modeling", "analyzed", "signaling")
                     if re.search(r"\b%s" % w, cuerpo_ref)]
    check("prosa", "inglés británico consistente", not americanismos,
          "revisar: %s" % americanismos if americanismos else "")

    refs = [l for l in lista_ref.split("\n") if re.match(r"^[A-Z][\w'-]+,", l.strip())]
    con_doi = [r for r in refs if "DOI: https://doi.org/" in r]
    check("prosa", "toda referencia lleva DOI en forma Ubiquity", len(con_doi) == len(refs),
          "%d de %d" % (len(con_doi), len(refs)))

    # ------------------------------------------------------ directrices de JCAA
    # Reglas tomadas de las Author Guidelines del portal y del precedente del
    # manuscrito del paper 3, ya en el sistema de la revista.
    print("\n4b. DIRECTRICES DE JCAA")
    try:
        i_ab = ps.index("Abstract")
        i_kw = ps.index("Keywords")
        n_abs = len(" ".join(ps[i_ab + 1:i_kw]).split())
        check("jcaa", "resumen de 250 palabras como máximo (JAS)", n_abs <= 250, "%d" % n_abs)
    except ValueError:
        check("jcaa", "resumen de 300 palabras como máximo", False, "sin sección Abstract")

    palabras_total = sum(len(p.split()) for p in ps)
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                palabras_total += len(c.text.split())
    check("jcaa", "8 500 palabras como máximo, referencias incluidas",
          palabras_total <= 8500, "%d" % palabras_total)

    # Harvard: sin coma entre autor y año en las citas parentéticas
    # la coma antes del ano delata APA tanto si cierra parentesis como si sigue
    # otra cita: «(DeMillo, Lipton, & Sayward, 1978; …)» se escapaba del patron
    # anterior porque tras el ano venia «;»
    apa = re.findall(r"[A-Z][A-Za-z]+, \d{4}[;)]", cuerpo_ref)
    check("jcaa", "citas Harvard, sin coma antes del año", not apa,
          "quedan: %s" % apa[:3] if apa else "")

    # referencias con año sin paréntesis (estilo Ubiquity: «Marwick, B 2016 …»).
    # El patron exige «(AAAA).» para no confundirse con numeros de fasciculo
    # como «314(5807):», que tambien tienen cuatro cifras entre parentesis.
    apa_ref = [r[:44] for r in refs if re.search(r"\((19|20)\d{2}\)\.", r)]
    check("jcaa", "referencias con el año sin paréntesis", not apa_ref,
          "quedan: %s" % apa_ref[:2] if apa_ref else "")

    # encabezados numerados, tres niveles como máximo
    niveles = {t.count(".") for t in (p.text.strip() for p in doc.paragraphs)
               if re.match(r"^\d+(\.\d+){0,3}\.?\s+[A-Z]", t or "")}
    check("jcaa", "encabezados numerados de hasta tres niveles",
          all(n <= 3 for n in niveles) if niveles else False,
          "profundidades: %s" % sorted(niveles))

    # ------------------------------------------------- propiedades del fichero
    print("\n5. PROPIEDADES DEL FICHERO")
    cp = doc.core_properties
    rastro = [k for k in ("author", "last_modified_by", "comments", "category",
                          "subject", "keywords")
              if (getattr(cp, k, "") or "").strip()]
    check("fichero", "sin autor ni rastro del generador", not rastro,
          "con contenido: %s" % rastro if rastro else "")
    with zipfile.ZipFile(DOCX) as z:
        crudo = (z.read("docProps/core.xml") + z.read("docProps/app.xml")).decode("utf-8")
    sospechas = [w for w in ("python-docx", "Macintosh", "Mamani", "Alanoca") if w in crudo]
    check("fichero", "los metadatos XML no delatan nada", not sospechas,
          "%s" % sospechas if sospechas else "")
    try:
        check("fichero", "fecha de creación verosímil", cp.created.year >= 2026,
              "%s" % cp.created.year)
    except Exception:
        check("fichero", "fecha de creación verosímil", False, "ilegible")

    print("\n" + "=" * 70)
    print("RESULTADO: %d comprobaciones correctas, %d fallos" % (ok_n, fail_n))
    print("=" * 70)
    json.dump({"ok": ok_n, "fallos": fail_n, "items": items},
              open(os.path.join(RES, "auditoria.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    return 1 if fail_n else 0


if __name__ == "__main__":
    sys.exit(main())
