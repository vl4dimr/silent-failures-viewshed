# -*- coding: utf-8 -*-
"""Corre el banco de pruebas contra gdal_viewshed, un motor de uso real.

El banco de p01 mide un motor propio con defectos inyectados. Eso demuestra
que el banco detecta defectos, pero no dice nada sobre las herramientas que
la arqueologia usa de verdad. Fisher (1993) observo que implementaciones
independientes del mismo viewshed discrepan sin que ninguna parezca rota;
este guion convierte esa observacion en una medida.

Motor evaluado aqui: gdal_viewshed, la utilidad de linea de ordenes de GDAL
que QGIS distribuye en su carpeta bin. Se invoca el ejecutable directamente,
no a traves de qgis_process ni del marco Processing de QGIS: lo que se mide
son los valores por defecto del programa, no los del dialogo de QGIS (que
tiene los suyos).

Cada caso del banco es una franja de 3 x n celdas de 30 m con el observador
en la columna 0 y el objetivo en la ultima. Se escribe como GeoTIFF, se corre
el motor y se lee el veredicto en la celda del objetivo.

Corridas por caso:

  configurado   -oz h_obs -tz h_tgt -cc 1-k, las alturas del estudio y el
                coeficiente que reproduce R/(1-k) con k = 0.13
  de fabrica    solo los argumentos obligatorios (-ox -oy entrada salida):
                todo lo demas queda en lo que el programa trae
  atribucion    de fabrica mas UN parametro devuelto al valor del estudio, para
                saber a cual se debe cada fallo

Salida: results/motores_reales.json
Uso:    python scripts/p07_motores_reales.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite                                    # noqa: E402
from los_engine import K_REFRACTION             # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
QGIS = Path(r"C:\Program Files\QGIS 3.44.13")
GDAL_VIEWSHED = QGIS / "bin" / "gdal_viewshed.exe"
GDALINFO = QGIS / "bin" / "gdalinfo.exe"

# GDAL aplica la correccion como cc * d^2/(2R). El motor del paper usa
# R_ef = R/(1-k) con k = 0.13, o sea (1-k) * d^2/(2R). Para comparar lo mismo
# hay que pasarle cc = 1-k, no el 0.85714 (= 1 - 1/7) que trae por defecto.
CC = 1.0 - K_REFRACTION

ENTORNO = dict(os.environ)
ENTORNO["PATH"] = str(QGIS / "bin") + os.pathsep + ENTORNO.get("PATH", "")
ENTORNO["GDAL_DATA"] = str(QGIS / "share" / "gdal")
ENTORNO["PROJ_LIB"] = str(QGIS / "share" / "proj")

# Lo que gdal_viewshed trae de fabrica, leido de `gdal_viewshed --long-usage`
# y de https://gdal.org/programs/gdal_viewshed.html (GDAL 3.13). El -tz 0 es,
# literalmente, el defecto «altura del objetivo nula» de la Tabla 1. El -cc
# 0.85714 (curvatura y refraccion con k = 1/7) esta activo por defecto desde
# GDAL 3.4. Ninguno se pasa en la corrida de fabrica: se dejan implicitos.
DEFECTOS_DE_FABRICA = dict(oz=2.0, tz=0.0, cc=0.85714)
DEFAULTS_DOCUMENTADOS = dict(
    oz=2.0, tz=0.0, cc=0.85714, md="sin limite", vv=255, iv=0, ov=0, om="NORMAL",
    obligatorios=["-ox", "-oy", "<src_filename>", "<dst_filename>"],
    fuente="gdal_viewshed --long-usage (GDAL 3.13.2) y gdal.org/programs/gdal_viewshed.html")


def version_gdal() -> str:
    r = subprocess.run([str(GDALINFO), "--version"], capture_output=True, text=True,
                       env=ENTORNO, timeout=60)
    return (r.stdout or r.stderr).strip()


def escribir_geotiff(dem: np.ndarray, ruta: Path, res: float) -> None:
    """DEM como GeoTIFF con georreferencia metrica simple."""
    import rasterio
    from rasterio.transform import from_origin
    alto, ancho = dem.shape
    perfil = dict(driver="GTiff", height=alto, width=ancho, count=1,
                  dtype="float32", crs="EPSG:32719",     # UTM 19S, zona del Titicaca
                  transform=from_origin(0.0, alto * res, res, res),
                  nodata=-9999.0)
    with rasterio.open(ruta, "w", **perfil) as dst:
        dst.write(dem.astype("float32"), 1)


def gdal_viewshed(dem, res, c0, r0, c1, r1, tmp: Path, oz=None, tz=None, cc=None):
    """¿Ve el observador (c0,r0) al objetivo (c1,r1) según gdal_viewshed?

    Los parametros a None se omiten y el programa usa su valor de fabrica. La
    salida se lee con la codificacion por defecto (visible = 255).
    Devuelve (veredicto, error, argumentos).
    """
    import rasterio
    ent, sal = tmp / "dem.tif", tmp / "vs.tif"
    escribir_geotiff(dem, ent, res)

    # centro de la celda del observador, en coordenadas del mundo
    alto = dem.shape[0]
    ox = (c0 + 0.5) * res
    oy = (alto - r0 - 0.5) * res

    args = ["-ox", f"{ox:.6f}", "-oy", f"{oy:.6f}"]
    if oz is not None:
        args += ["-oz", f"{oz:.4f}"]
    if tz is not None:
        args += ["-tz", f"{tz:.4f}"]
    if cc is not None:
        args += ["-cc", f"{cc:.6f}"]
    cmd = [str(GDAL_VIEWSHED)] + args + [str(ent), str(sal)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENTORNO, timeout=180)
    if r.returncode != 0 or not sal.exists():
        return None, (r.stderr or r.stdout)[:200], " ".join(args)
    with rasterio.open(sal) as src:
        v = int(src.read(1)[r1, c1])
    for f in (ent, sal):
        f.unlink(missing_ok=True)
    return v == DEFAULTS_DOCUMENTADOS["vv"], None, " ".join(args)


def main():
    if not GDAL_VIEWSHED.exists():
        sys.exit(f"no se encontro gdal_viewshed en {GDAL_VIEWSHED}")
    ver = version_gdal()

    filas, err = [], 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for c in suite.casos_detallados():
            dem, res, c0, r0, c1, r1, h_obs, h_tgt = suite.geometria(c)
            esperado = bool(c["esperado"])
            conf, fallo, args_conf = gdal_viewshed(dem, res, c0, r0, c1, r1, tmp,
                                                   oz=h_obs, tz=h_tgt, cc=CC)
            fab, fallo_f, args_fab = gdal_viewshed(dem, res, c0, r0, c1, r1, tmp)
            # atribucion: de fabrica mas un solo parametro del estudio
            atrib = {}
            for clave, kw in (("oz", dict(oz=h_obs)), ("tz", dict(tz=h_tgt)),
                              ("cc", dict(cc=CC))):
                v, _, _ = gdal_viewshed(dem, res, c0, r0, c1, r1, tmp, **kw)
                atrib[clave] = (v == esperado) if v is not None else None
            if conf is None or fab is None:
                err += 1
            filas.append(dict(
                caso=c["nombre"], esperado=esperado,
                gdal=conf, coincide=(conf == esperado) if conf is not None else None,
                gdal_fabrica=fab,
                coincide_fabrica=(fab == esperado) if fab is not None else None,
                nota=fallo or fallo_f,
                atribucion_coincide=atrib,
                distancia_km=(c1 - c0) * res / 1000.0, h_obs=h_obs, h_tgt=h_tgt,
                argumentos_configurado=args_conf, argumentos_de_fabrica=args_fab))

    n = len(filas)
    ok = sum(1 for f in filas if f.get("coincide") is True)
    mal = sum(1 for f in filas if f.get("coincide") is False)
    ok_f = sum(1 for f in filas if f.get("coincide_fabrica") is True)
    mal_f = sum(1 for f in filas if f.get("coincide_fabrica") is False)
    atrib_res = {k: dict(coinciden=sum(1 for f in filas if f["atribucion_coincide"][k] is True),
                         de=n,
                         descripcion="de fabrica, salvo -%s devuelto al valor del estudio" % k)
                 for k in ("oz", "tz", "cc")}
    res = dict(
        motor="gdal_viewshed (GDAL %s, binarios de QGIS 3.44.13)" % ver.split()[1],
        version_gdal=ver, distribucion="QGIS 3.44.13",
        invocacion=("ejecutable gdal_viewshed.exe llamado directamente por subprocess; "
                    "no se usa qgis_process ni el marco Processing de QGIS"),
        cc_ajustado=CC,
        parametros_de_fabrica=DEFECTOS_DE_FABRICA,
        defaults_documentados=DEFAULTS_DOCUMENTADOS,
        corridas=dict(
            configurado=dict(argumentos="-ox -oy -oz h_obs -tz h_tgt -cc %.2f <src> <dst>" % CC,
                             descripcion="alturas del estudio y curvatura+refraccion con k = 0.13"),
            de_fabrica=dict(argumentos="-ox -oy <src> <dst>",
                            descripcion="solo los argumentos obligatorios; -oz, -tz y -cc "
                                        "quedan en sus valores de fabrica (2, 0, 0.85714)"),
            atribucion="de fabrica mas un solo parametro (-oz, -tz o -cc) al valor del estudio"),
        casos=n,
        ajustado=dict(coinciden=ok, discrepan=mal),
        de_fabrica=dict(coinciden=ok_f, discrepan=mal_f),
        atribucion=atrib_res,
        errores=err, detalle=filas)
    salida = RAIZ / "results" / "motores_reales.json"
    salida.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 72)
    print(f"BANCO DE PRUEBAS contra {res['motor']}   (cc configurado = {CC:.3f})")
    print("=" * 72)
    for f in filas:
        m1 = {True: "coincide", False: "DISCREPA", None: "error   "}[f.get("coincide")]
        m2 = {True: "coincide", False: "DISCREPA", None: "error   "}[f.get("coincide_fabrica")]
        esp = "visible" if f["esperado"] else "tapado "
        print(f"  conf:{m1}  fab:{m2}  esperado={esp}  {f['caso'][:52]}")
        if f.get("nota"):
            print(f"            {f['nota'][:66]}")
    print(f"\nconfigurado {ok}/{n} | de fabrica {ok_f}/{n} | errores {err}")
    for k, v in atrib_res.items():
        print(f"  atribucion -{k}: {v['coinciden']}/{n} coinciden")
    print(f"\nGuardado: {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
