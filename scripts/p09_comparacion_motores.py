# -*- coding: utf-8 -*-
"""Consolida el banco contra motores reales y mide su discrepancia.

Fisher (1993) observo que implementaciones independientes del mismo viewshed
discrepan sin que ninguna parezca rota. Aqui esa observacion se convierte en
una medida: dos motores de uso masivo en arqueologia —gdal_viewshed y
r.viewshed, ambos distribuidos con QGIS e invocados directamente— se corren
contra el mismo banco de respuesta derivada, una vez con los parametros del
estudio y otra con solo sus argumentos obligatorios (todo lo demas de fabrica).

El hallazgo no es que los motores esten rotos: los dos pasan el banco entero
cuando se les configura. Es que sus valores por defecto reproducen defectos
documentados. Este guion cuenta, sin presuponer la direccion, en que casos
falla cada uno de fabrica, hacia donde, en cuales discrepan entre si y en
cuales coinciden en el mismo error. Tambien recoge la atribucion de cada fallo
a un parametro concreto, medida en p07 y p08.

Salida: results/comparacion_motores.json
Uso:    python scripts/p09_comparacion_motores.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "results"


def cargar(nombre):
    return json.loads((RES / nombre).read_text(encoding="utf-8"))


gdal = cargar("motores_reales.json")
grass = cargar("grass_viewshed.json")

# indexar por caso
g1 = {f["caso"]: f for f in gdal["detalle"]}
g2 = {f["caso"]: f for f in grass["detalle"]}
casos = [f["caso"] for f in gdal["detalle"]]


def sentido(obtenido, esperado):
    """Direccion del fallo de un veredicto, o None si acierta."""
    if obtenido is None or obtenido == esperado:
        return None
    return "declara_tapado_lo_visible" if esperado else "declara_visible_lo_tapado"


filas = []
for c in casos:
    a, b = g1.get(c, {}), g2.get(c, {})
    esp = a.get("esperado")
    filas.append(dict(
        caso=c,
        esperado=esp,
        distancia_km=a.get("distancia_km"), h_obs=a.get("h_obs"), h_tgt=a.get("h_tgt"),
        gdal_correcto=a.get("gdal"),
        gdal_fabrica=a.get("gdal_fabrica"),
        grass_correcto=b.get("configurado"),
        grass_fabrica=b.get("de_fabrica"),
        fallo_gdal_fabrica=sentido(a.get("gdal_fabrica"), esp),
        fallo_grass_fabrica=sentido(b.get("de_fabrica"), esp),
        atribucion_gdal=a.get("atribucion_coincide"),
        atribucion_grass=b.get("atribucion_coincide"),
    ))

n = len(filas)


def cuenta(clave, ref="esperado"):
    return sum(1 for f in filas if f[clave] is not None and f[clave] == f[ref])


def direccion(clave):
    fn = sum(1 for f in filas if f[clave] is False and f["esperado"] is True)
    fp = sum(1 for f in filas if f[clave] is True and f["esperado"] is False)
    return dict(declara_tapado_lo_visible=fn, declara_visible_lo_tapado=fp)


def fallan(clave):
    return [f["caso"] for f in filas if f[clave] is not None and f[clave] != f["esperado"]]


# discrepancia entre motores con sus valores de fabrica, y en que coinciden
discrepan = [f for f in filas
             if f["gdal_fabrica"] is not None and f["grass_fabrica"] is not None
             and f["gdal_fabrica"] != f["grass_fabrica"]]
mismo_error = [f for f in filas
               if f["fallo_gdal_fabrica"] is not None
               and f["fallo_gdal_fabrica"] == f["fallo_grass_fabrica"]]
ambos_aciertan = [f for f in filas
                  if f["gdal_fabrica"] == f["esperado"] and f["grass_fabrica"] == f["esperado"]]


def atribucion(motor, clave):
    return {k: dict(coinciden=v["coinciden"], de=v["de"], descripcion=v["descripcion"])
            for k, v in motor["atribucion"].items()}


res = dict(
    banco="%d casos de terreno con respuesta derivada (suite.py, p01)" % n,
    invocacion=("ejecutables llamados directamente: gdal_viewshed.exe y grass85.bat --exec; "
                "no se usa qgis_process ni el marco Processing de QGIS, cuyos dialogos "
                "tienen valores por defecto propios que aqui no se miden"),
    de_fabrica_significa="solo los argumentos obligatorios de cada programa; nada mas se pasa",
    motores={
        "GDAL gdal_viewshed": dict(
            # "version" conserva el formato que lee el manuscrito (la distribucion);
            # la version de la biblioteca va en version_gdal
            version=gdal["distribucion"],
            version_gdal=gdal["version_gdal"].split()[1],
            biblioteca=gdal["version_gdal"],
            distribucion=gdal["distribucion"],
            correcto=f"{cuenta('gdal_correcto')}/{n}",
            de_fabrica=f"{cuenta('gdal_fabrica')}/{n}",
            defecto_de_fabrica=("-tz 0 (altura del objetivo nula); -oz 2; -cc 0.85714 "
                                "(curvatura y refraccion activas por defecto desde GDAL 3.4)"),
            parametros_configurado=gdal["corridas"]["configurado"]["argumentos"],
            parametros_de_fabrica=gdal["corridas"]["de_fabrica"]["argumentos"],
            defaults_documentados=gdal["defaults_documentados"],
            direccion=direccion("gdal_fabrica"),
            casos_que_falla_de_fabrica=fallan("gdal_fabrica"),
            atribucion=atribucion(gdal, "gdal")),
        "GRASS r.viewshed": dict(
            version=grass["version_grass"].split()[1],
            biblioteca=grass["version_grass"],
            distribucion=grass["distribucion"],
            correcto=f"{cuenta('grass_correcto')}/{n}",
            de_fabrica=f"{cuenta('grass_fabrica')}/{n}",
            defecto_de_fabrica=("target_elevation 0.0 (altura del objetivo nula); "
                                "observer_elevation 1.75; sin -c ni -r (curvatura y "
                                "refraccion omitidas)"),
            parametros_configurado=grass["corridas"]["configurado"]["orden"],
            parametros_de_fabrica=grass["corridas"]["de_fabrica"]["orden"],
            defaults_documentados=grass["defaults_documentados"],
            elipsoide=grass["elipsoide"],
            comprobacion_refraccion=grass["comprobacion_refraccion"],
            direccion=direccion("grass_fabrica"),
            casos_que_falla_de_fabrica=fallan("grass_fabrica"),
            atribucion=atribucion(grass, "grass")),
    },
    discrepancia_entre_motores_de_fabrica=dict(
        casos=len(discrepan),
        de=n,
        detalle=[d["caso"] for d in discrepan],
        detalle_direccion=[dict(caso=d["caso"], esperado=d["esperado"],
                                gdal_fabrica=d["gdal_fabrica"], grass_fabrica=d["grass_fabrica"],
                                acierta=("GDAL" if d["gdal_fabrica"] == d["esperado"] else "GRASS"))
                           for d in discrepan],
        acierta_gdal=sum(1 for d in discrepan if d["gdal_fabrica"] == d["esperado"]),
        acierta_grass=sum(1 for d in discrepan if d["grass_fabrica"] == d["esperado"])),
    coincidencia_en_el_error_de_fabrica=dict(
        casos=len(mismo_error), de=n,
        detalle=[dict(caso=f["caso"], sentido=f["fallo_gdal_fabrica"]) for f in mismo_error],
        descripcion="casos en que ambos motores de fabrica fallan con el mismo veredicto"),
    ambos_aciertan_de_fabrica=dict(casos=len(ambos_aciertan), de=n),
    detalle=filas,
)
(RES / "comparacion_motores.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("=" * 78)
print("DOS MOTORES DE USO REAL CONTRA EL MISMO BANCO")
print("=" * 78)
for nombre, m in res["motores"].items():
    print(f"\n{nombre} ({m['biblioteca']}, {m['distribucion']})")
    print(f"   configurado               : {m['correcto']}")
    print(f"   de fabrica                : {m['de_fabrica']}")
    print(f"   defecto de fabrica        : {m['defecto_de_fabrica']}")
    d = m["direccion"]
    print(f"   falsos negativos (tapa lo que se ve)    : {d['declara_tapado_lo_visible']}")
    print(f"   falsos positivos (ve lo que esta tapado): {d['declara_visible_lo_tapado']}")
    for k, v in m["atribucion"].items():
        print(f"   {v['descripcion']:<58}: {v['coinciden']}/{v['de']}")

dd = res["discrepancia_entre_motores_de_fabrica"]
print(f"\nDISCREPAN ENTRE SI, de fabrica: {dd['casos']} de {dd['de']} casos "
      f"(acierta GDAL en {dd['acierta_gdal']}, GRASS en {dd['acierta_grass']})")
for c in dd["detalle_direccion"]:
    print(f"   - {c['caso'][:60]}  -> acierta {c['acierta']}")
ce = res["coincidencia_en_el_error_de_fabrica"]
print(f"COINCIDEN EN EL MISMO ERROR, de fabrica: {ce['casos']} de {ce['de']}")
for c in ce["detalle"]:
    print(f"   - {c['caso'][:60]}  ({c['sentido']})")
print(f"AMBOS ACIERTAN de fabrica: {res['ambos_aciertan_de_fabrica']['casos']} de {n}")
print(f"\nGuardado: results/comparacion_motores.json")
