# -*- coding: utf-8 -*-
"""Corre el banco de pruebas contra GRASS r.viewshed.

GRASS es, junto con GDAL, el motor de visibilidad que la arqueologia usa por
debajo de QGIS. Interesa por dos motivos: es una implementacion independiente
de la de GDAL —lo que permite medir la discrepancia que observo Fisher (1993)
en lugar de solo citarla— y porque sus valores de fabrica son otros: la
curvatura terrestre solo se aplica con la bandera -c, la refraccion solo con
-r (refraction_coeff no hace nada sin ella), y el objetivo va a ras de suelo
(target_elevation=0.0) con el observador a 1.75 m.

Se invoca GRASS directamente (grass85.bat --exec), no a traves de qgis_process
ni del marco Processing de QGIS. Con -c, r.viewshed usa como radio el semieje
mayor del elipsoide de la localizacion (a = 6378137 m para EPSG:32719) y, con
-r, lo divide por (1 - refraction_coeff): la misma convencion que el motor del
articulo, con R = 6371000 m en lugar de a.

Corridas por caso:

  configurado   observer_elevation=h_obs target_elevation=h_tgt -c -r
                refraction_coeff=0.13
  de fabrica    solo input, output y coordinates
  atribucion    de fabrica mas UN parametro devuelto al valor del estudio

Y una comprobacion aparte: sobre un plano cerca de la distancia critica,
-c sin -r y -c -r refraction_coeff=0.13 tienen que dar veredictos distintos
(la primera version de este guion pasaba refraction_coeff sin -r y media
curvatura sin refraccion sin saberlo).

Salida: results/grass_viewshed.json
Uso:    python scripts/p08_grass_viewshed.py
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite                                    # noqa: E402
from los_engine import K_REFRACTION, R_EARTH    # noqa: E402
from p07_motores_reales import escribir_geotiff  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
QGIS = Path(r"C:\Program Files\QGIS 3.44.13")
GRASS = QGIS / "bin" / "grass85.bat"
A_WGS84 = 6378137.0     # semieje mayor que r.viewshed usa como radio con -c

ENTORNO = dict(os.environ)
ENTORNO["PATH"] = str(QGIS / "bin") + os.pathsep + ENTORNO.get("PATH", "")
ENTORNO["GDAL_DATA"] = str(QGIS / "share" / "gdal")
ENTORNO["PROJ_LIB"] = str(QGIS / "share" / "proj")

# Leido de `r.viewshed --help` (GRASS 8.5.0) y del manual
# grass.osgeo.org/grass-stable/manuals/r.viewshed.html. Ninguno se pasa en la
# corrida de fabrica.
DEFAULTS_DOCUMENTADOS = dict(
    observer_elevation=1.75, target_elevation=0.0, max_distance=-1,
    refraction_coeff=0.14286, memory=500,
    flag_c="Consider the curvature of the earth (current ellipsoid); apagada por defecto",
    flag_r="Consider the effect of atmospheric refraction; apagada por defecto. Sin -r, "
           "refraction_coeff no tiene efecto (raster/r.viewshed/grass.cpp, "
           "adjust_for_curvature: if (!doRefr) return h - adjustment)",
    obligatorios=["input", "output", "coordinates"],
    fuente="r.viewshed --help (GRASS 8.5.0), manual en linea y grass.cpp")


def version_grass() -> str:
    r = subprocess.run([str(GRASS), "--version"], capture_output=True, text=True,
                       env=ENTORNO, timeout=120)
    for linea in (r.stdout or r.stderr).splitlines():
        if linea.strip().startswith("GRASS"):
            return linea.strip()
    return "GRASS (version no leida)"


def grass_viewshed(dem, res, c0, r0, c1, r1, base: Path, observer=None, target=None,
                   curvatura=False, refraccion=False, coef=None):
    """Veredicto de r.viewshed. Los parametros a None y las banderas a False se
    omiten: el modulo usa su valor de fabrica. Devuelve (veredicto, error, orden)."""
    trabajo = base / "gr"
    if trabajo.exists():
        shutil.rmtree(trabajo, ignore_errors=True)
    trabajo.mkdir(parents=True)

    tif = base / "dem.tif"
    escribir_geotiff(dem, tif, res)

    alto = dem.shape[0]
    ox = (c0 + 0.5) * res
    oy = (alto - r0 - 0.5) * res
    salida_txt = base / "vs.txt"
    if salida_txt.exists():
        salida_txt.unlink()

    args = [f"input=dem", f"output=vs", f"coordinates={ox},{oy}"]
    if observer is not None:
        args.append(f"observer_elevation={observer}")
    if target is not None:
        args.append(f"target_elevation={target}")
    if coef is not None:
        args.append(f"refraction_coeff={coef}")
    if curvatura:
        args.append("-c")
    if refraccion:
        args.append("-r")
    orden_vs = "r.viewshed " + " ".join(args)

    # r.viewshed escribe el mapa; se exporta la celda del objetivo con r.what
    orden = (
        f"r.in.gdal input={tif} output=dem --overwrite --quiet && "
        f"g.region raster=dem --quiet && "
        f"{orden_vs} --overwrite --quiet"
    )
    tx = (c1 + 0.5) * res
    ty = (alto - r1 - 0.5) * res

    guion = base / "run.bat"
    guion.write_text(
        f"@echo off\r\n{orden}\r\n"
        f"r.what map=vs coordinates={tx},{ty} > \"{salida_txt}\"\r\n",
        encoding="utf-8")

    cmd = [str(GRASS), "-c", str(tif), str(trabajo / "loc"), "--exec",
           "cmd", "/c", str(guion)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENTORNO,
                       timeout=300)
    if not salida_txt.exists():
        return None, ((r.stderr or r.stdout) or "sin salida")[-200:], orden_vs

    txt = salida_txt.read_text(encoding="utf-8", errors="ignore").strip()
    # formato: este|norte||valor   (vacio o '*' = no visible / nulo)
    campos = txt.split("|")
    valor = campos[-1].strip() if campos else ""
    salida_txt.unlink(missing_ok=True)
    shutil.rmtree(trabajo, ignore_errors=True)
    tif.unlink(missing_ok=True)

    if valor in ("", "*"):
        return False, None, orden_vs      # celda nula: fuera del viewshed
    try:
        return float(valor) >= 0.0, None, orden_vs
    except ValueError:
        return None, f"valor no interpretable: {valor!r}", orden_vs


def comprobacion_refraccion(base: Path, h_obs=1.7, h_tgt=3.0):
    """Sobre un plano, cerca de la distancia critica: ¿distingue GRASS -c de -c -r?

    Se anota ademas la distancia critica exacta que predice cada convencion de
    radio, para leer los veredictos contra ella.
    """
    res = suite.RES
    modos = [
        ("sin banderas", dict()),
        ("-c", dict(curvatura=True)),
        ("-c refraction_coeff=0.13 (sin -r; protocolo de la primera version)",
         dict(curvatura=True, coef=K_REFRACTION)),
        ("-c -r refraction_coeff=0.13", dict(curvatura=True, refraccion=True, coef=K_REFRACTION)),
        ("-c -r (refraction_coeff de fabrica, 0.14286)", dict(curvatura=True, refraccion=True)),
    ]
    kms = (10.5, 11.0, 11.3, 11.5, 11.7, 12.0)
    filas = []
    for etiqueta, kw in modos:
        veredictos = {}
        for km in kms:
            cols = int(round(km * 1000 / res))
            dem = suite.plano(cols + 2)
            v, e, _ = grass_viewshed(dem, res, 0, 1, cols, 1, base,
                                     observer=h_obs, target=h_tgt, **kw)
            veredictos["%.2f" % (cols * res / 1000)] = v
        filas.append(dict(modo=etiqueta, veredictos=veredictos))
    d = lambda r: suite.distancia_critica(h_obs, h_tgt, r) / 1000.0
    predicciones = {
        "sin curvatura": None,
        "-c (R = a = %.0f m)" % A_WGS84: d(A_WGS84),
        "-c -r 0.13 (R = a/(1-0.13))": d(A_WGS84 / (1 - K_REFRACTION)),
        "-c -r 0.14286 (R = a/(1-0.14286))": d(A_WGS84 / (1 - 0.14286)),
        "motor del articulo (R = %.0f/(1-0.13))" % R_EARTH: d(R_EARTH / (1 - K_REFRACTION)),
    }
    # la conclusion se calcula, no se escribe: -c y -c -r 0.13 deben diferir en algo
    con_c = filas[1]["veredictos"]
    con_c_sin_r = filas[2]["veredictos"]
    con_cr = filas[3]["veredictos"]
    return dict(
        h_obs=h_obs, h_tgt=h_tgt, distancias_km=list(con_c.keys()),
        corridas=filas, distancia_critica_predicha_km=predicciones,
        c_y_cr_difieren=any(con_c[k] != con_cr[k] for k in con_c),
        coef_sin_r_es_igual_que_c_solo=all(con_c[k] == con_c_sin_r[k] for k in con_c))


def main():
    if not GRASS.exists():
        sys.exit(f"no se encontro GRASS en {GRASS}")
    ver = version_grass()
    print(f"{ver}: comprobacion de -c frente a -c -r cerca de la distancia critica ...")

    filas, err = [], 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        refr = comprobacion_refraccion(base)
        for f in refr["corridas"]:
            print("  %-64s %s" % (f["modo"][:64],
                                  " ".join("%s:%s" % (k, "v" if v else "T")
                                           for k, v in f["veredictos"].items())))
        print("  -c y -c -r difieren: %s | refraction_coeff sin -r = -c solo: %s"
              % (refr["c_y_cr_difieren"], refr["coef_sin_r_es_igual_que_c_solo"]))

        for c in suite.casos_detallados():
            dem, res, c0, r0, c1, r1, h_obs, h_tgt = suite.geometria(c)
            esperado = bool(c["esperado"])
            conf, e1, orden_conf = grass_viewshed(dem, res, c0, r0, c1, r1, base,
                                                  observer=h_obs, target=h_tgt,
                                                  curvatura=True, refraccion=True,
                                                  coef=K_REFRACTION)
            fab, e2, orden_fab = grass_viewshed(dem, res, c0, r0, c1, r1, base)
            atrib = {}
            for clave, kw in (("observer_elevation", dict(observer=h_obs)),
                              ("target_elevation", dict(target=h_tgt)),
                              ("curvatura_y_refraccion",
                               dict(curvatura=True, refraccion=True, coef=K_REFRACTION))):
                v, _, _ = grass_viewshed(dem, res, c0, r0, c1, r1, base, **kw)
                atrib[clave] = (v == esperado) if v is not None else None
            if conf is None or fab is None:
                err += 1
            filas.append(dict(
                caso=c["nombre"], esperado=esperado,
                configurado=conf,
                coincide=(conf == esperado) if conf is not None else None,
                de_fabrica=fab,
                coincide_fabrica=(fab == esperado) if fab is not None else None,
                nota=e1 or e2,
                atribucion_coincide=atrib,
                distancia_km=(c1 - c0) * res / 1000.0, h_obs=h_obs, h_tgt=h_tgt,
                orden_configurado=orden_conf, orden_de_fabrica=orden_fab))

    n = len(filas)
    ok = sum(1 for f in filas if f.get("coincide") is True)
    okf = sum(1 for f in filas if f.get("coincide_fabrica") is True)
    atrib_res = {k: dict(coinciden=sum(1 for f in filas if f["atribucion_coincide"][k] is True),
                         de=n, descripcion="de fabrica, salvo %s al valor del estudio" % k)
                 for k in ("observer_elevation", "target_elevation", "curvatura_y_refraccion")}
    res = dict(
        motor="GRASS r.viewshed %s (binarios de QGIS 3.44.13)" % ver.split()[1],
        version_grass=ver, distribucion="QGIS 3.44.13",
        invocacion=("grass85.bat -c <tif> <loc> --exec cmd /c run.bat, con r.in.gdal, g.region, "
                    "r.viewshed y r.what; no se usa qgis_process ni el marco Processing de QGIS"),
        elipsoide=("localizacion creada desde el GeoTIFF en EPSG:32719 (WGS 84): con -c "
                   "r.viewshed usa a = %.0f m como radio" % A_WGS84),
        nota_curvatura=("r.viewshed no aplica curvatura salvo con -c, ni refraccion salvo "
                        "con -r; refraction_coeff no tiene efecto sin -r"),
        defaults_documentados=DEFAULTS_DOCUMENTADOS,
        corridas=dict(
            configurado=dict(orden="r.viewshed input output coordinates observer_elevation=h_obs "
                                   "target_elevation=h_tgt refraction_coeff=%s -c -r" % K_REFRACTION,
                             descripcion="alturas del estudio, curvatura y refraccion con k = 0.13"),
            de_fabrica=dict(orden="r.viewshed input output coordinates",
                            descripcion="solo los parametros obligatorios; observer 1.75, "
                                        "target 0.0, sin -c ni -r"),
            atribucion="de fabrica mas un solo parametro al valor del estudio"),
        comprobacion_refraccion=refr,
        casos=n,
        configurado=dict(coinciden=ok, discrepan=n - ok - err),
        de_fabrica=dict(coinciden=okf, discrepan=n - okf),
        atribucion=atrib_res,
        errores=err, detalle=filas)
    (RAIZ / "results" / "grass_viewshed.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 74)
    print(f"BANCO DE PRUEBAS contra {res['motor']}")
    print("=" * 74)
    print(f"{'config.':>8} {'fabrica':>9}   caso")
    for f in filas:
        m1 = {True: "   ok   ", False: " FALLA  ", None: " error  "}[f.get("coincide")]
        m2 = {True: "   ok   ", False: " FALLA  ", None: " error  "}[f.get("coincide_fabrica")]
        print(f"{m1} {m2}   {f['caso'][:52]}")
        if f.get("nota"):
            print(f"          {f['nota'][:64]}")
    print(f"\n  configurado (-c -r, alturas del estudio): {ok}/{n}")
    print(f"  de fabrica (solo obligatorios)          : {okf}/{n}")
    for k, v in atrib_res.items():
        print(f"  atribucion {k}: {v['coinciden']}/{n} coinciden")
    print(f"  errores                                 : {err}")


if __name__ == "__main__":
    main()
