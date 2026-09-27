# -*- coding: utf-8 -*-
"""Consolida el banco contra motores reales y mide su discrepancia.

Fisher (1993) observo que implementaciones independientes del mismo viewshed
discrepan sin que ninguna parezca rota. Aqui esa observacion se convierte en
una medida: dos motores de uso masivo en arqueologia —GDAL y GRASS, ambos
accesibles desde QGIS— se corren contra el mismo banco de respuesta conocida,
una vez con los parametros correctos y otra con sus valores de fabrica.

El hallazgo no es que los motores esten rotos: los dos pasan el banco entero
cuando se les configura bien. Es que sus valores por defecto reproducen
defectos documentados, y lo hacen en direcciones opuestas.

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

filas = []
for c in casos:
    a, b = g1.get(c, {}), g2.get(c, {})
    filas.append(dict(
        caso=c,
        esperado=a.get("esperado"),
        gdal_correcto=a.get("gdal"),
        gdal_fabrica=a.get("gdal_fabrica"),
        grass_correcto=b.get("con_curvatura"),
        grass_fabrica=b.get("de_fabrica"),
    ))

n = len(filas)
def cuenta(clave, ref="esperado"):
    return sum(1 for f in filas if f[clave] is not None and f[clave] == f[ref])

# discrepancia entre motores con sus valores de fabrica
discrepan = [f for f in filas
             if f["gdal_fabrica"] is not None and f["grass_fabrica"] is not None
             and f["gdal_fabrica"] != f["grass_fabrica"]]

# direccion del fallo de cada uno
def direccion(clave):
    fn = sum(1 for f in filas if f[clave] is False and f["esperado"] is True)
    fp = sum(1 for f in filas if f[clave] is True and f["esperado"] is False)
    return dict(declara_tapado_lo_visible=fn, declara_visible_lo_tapado=fp)

res = dict(
    banco="15 casos de terreno con respuesta derivada",
    motores={
        "GDAL gdal_viewshed": dict(
            version="QGIS 3.44.13",
            correcto=f"{cuenta('gdal_correcto')}/{n}",
            de_fabrica=f"{cuenta('gdal_fabrica')}/{n}",
            defecto_de_fabrica="-tz = 0 (altura del objetivo nula)",
            direccion=direccion("gdal_fabrica")),
        "GRASS r.viewshed": dict(
            version="8.5.0",
            correcto=f"{cuenta('grass_correcto')}/{n}",
            de_fabrica=f"{cuenta('grass_fabrica')}/{n}",
            defecto_de_fabrica="sin -c (curvatura terrestre omitida)",
            direccion=direccion("grass_fabrica")),
    },
    discrepancia_entre_motores_de_fabrica=dict(
        casos=len(discrepan),
        de=n,
        detalle=[d["caso"] for d in discrepan]),
    detalle=filas,
)
(RES / "comparacion_motores.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

print("=" * 78)
print("DOS MOTORES DE USO REAL CONTRA EL MISMO BANCO")
print("=" * 78)
for nombre, m in res["motores"].items():
    print(f"\n{nombre} ({m['version']})")
    print(f"   configurado correctamente : {m['correcto']}")
    print(f"   con valores de fabrica    : {m['de_fabrica']}")
    print(f"   defecto de fabrica        : {m['defecto_de_fabrica']}")
    d = m["direccion"]
    print(f"   falsos negativos (tapa lo que se ve)  : {d['declara_tapado_lo_visible']}")
    print(f"   falsos positivos (ve lo que esta tapado): {d['declara_visible_lo_tapado']}")

dd = res["discrepancia_entre_motores_de_fabrica"]
print(f"\nDISCREPANCIA ENTRE AMBOS, con sus valores de fabrica: "
      f"{dd['casos']} de {dd['de']} casos")
for c in dd["detalle"]:
    print(f"   - {c[:66]}")
print(f"\nGuardado: results/comparacion_motores.json")
