# -*- coding: utf-8 -*-
"""Corre el banco de pruebas contra motores de visibilidad de uso real.

El banco de p01 mide un motor propio con defectos inyectados. Eso demuestra
que el banco detecta defectos, pero no dice nada sobre las herramientas que
la arqueologia usa de verdad. Fisher (1993) observo que implementaciones
independientes del mismo viewshed discrepan sin que ninguna parezca rota;
este guion convierte esa observacion en una medida, que es lo que el propio
manuscrito propone como trabajo futuro.

Motor evaluado aqui: gdal_viewshed, el que QGIS expone como «Viewshed» de
GDAL y el que acaba usando buena parte de los estudios de visibilidad.

Cada caso del banco es una franja de 3 x n celdas de 30 m con el observador
en la columna 0 y el objetivo en la ultima. Se escribe como GeoTIFF, se corre
el motor y se lee el veredicto en la celda del objetivo.

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

# GDAL aplica la correccion como cc * d^2/(2R). El motor del paper usa
# R_ef = R/(1-k) con k = 0.13, o sea (1-k) * d^2/(2R). Para comparar lo mismo
# hay que pasarle cc = 1-k, no el 0.85714 que trae por defecto.
CC = 1.0 - K_REFRACTION

ENTORNO = dict(os.environ)
ENTORNO["PATH"] = str(QGIS / "bin") + os.pathsep + ENTORNO.get("PATH", "")
ENTORNO["GDAL_DATA"] = str(QGIS / "share" / "gdal")
ENTORNO["PROJ_LIB"] = str(QGIS / "share" / "proj")


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


# Lo que trae gdal_viewshed de fabrica. El -tz = 0 es, literalmente, el
# defecto «altura del objetivo nula» que la Tabla 1 clasificaba como
# «plausible default»: no es plausible, es el valor por defecto real.
DEFECTOS_DE_FABRICA = dict(oz=2.0, tz=0.0, cc=0.85714)


def gdal_viewshed(dem, res, c0, r0, c1, r1, h_obs, h_tgt, tmp: Path,
                  de_fabrica=False):
    """¿Ve el observador (c0,r0) al objetivo (c1,r1) según gdal_viewshed?"""
    if de_fabrica:
        h_obs = DEFECTOS_DE_FABRICA["oz"]
        h_tgt = DEFECTOS_DE_FABRICA["tz"]
    import rasterio
    ent, sal = tmp / "dem.tif", tmp / "vs.tif"
    escribir_geotiff(dem, ent, res)

    # centro de la celda del observador, en coordenadas del mundo
    alto = dem.shape[0]
    ox = (c0 + 0.5) * res
    oy = (alto - r0 - 0.5) * res

    cmd = [str(GDAL_VIEWSHED), "-q",
           "-ox", f"{ox:.6f}", "-oy", f"{oy:.6f}",
           "-oz", f"{h_obs:.4f}", "-tz", f"{h_tgt:.4f}",
           "-cc", f"{DEFECTOS_DE_FABRICA['cc'] if de_fabrica else CC:.6f}",
           "-vv", "1", "-iv", "0", "-ov", "0",
           "-om", "NORMAL", str(ent), str(sal)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENTORNO, timeout=180)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout)[:200]
    with rasterio.open(sal) as src:
        v = src.read(1)[r1, c1]
    for f in (ent, sal):
        f.unlink(missing_ok=True)
    return bool(v == 1), None


def main():
    if not GDAL_VIEWSHED.exists():
        sys.exit(f"no se encontro gdal_viewshed en {GDAL_VIEWSHED}")

    casos = suite.casos()
    filas, err = [], 0

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for nombre, fn, esperado in casos:
            # se reconstruye la geometria del caso ejecutandolo con trazas
            geo = _geometria_del_caso(fn)
            if geo is None:
                filas.append(dict(caso=nombre, esperado=esperado,
                                  gdal=None, nota="geometria no extraible"))
                continue
            dem, res, c0, r0, c1, r1, h_obs, h_tgt = geo
            obtenido, fallo = gdal_viewshed(dem, res, c0, r0, c1, r1,
                                            h_obs, h_tgt, tmp)
            fabrica, _ = gdal_viewshed(dem, res, c0, r0, c1, r1,
                                       h_obs, h_tgt, tmp, de_fabrica=True)
            if obtenido is None:
                err += 1
            filas.append(dict(caso=nombre, esperado=bool(esperado),
                              gdal=obtenido, coincide=(obtenido == bool(esperado))
                              if obtenido is not None else None,
                              gdal_fabrica=fabrica,
                              coincide_fabrica=(fabrica == bool(esperado))
                              if fabrica is not None else None,
                              nota=fallo))

    ok = sum(1 for f in filas if f.get("coincide") is True)
    mal = sum(1 for f in filas if f.get("coincide") is False)
    ok_f = sum(1 for f in filas if f.get("coincide_fabrica") is True)
    mal_f = sum(1 for f in filas if f.get("coincide_fabrica") is False)
    res = dict(motor="gdal_viewshed (QGIS 3.44.13)", cc_ajustado=CC,
               parametros_de_fabrica=DEFECTOS_DE_FABRICA,
               casos=len(filas),
               ajustado=dict(coinciden=ok, discrepan=mal),
               de_fabrica=dict(coinciden=ok_f, discrepan=mal_f),
               errores=err, detalle=filas)
    salida = RAIZ / "results" / "motores_reales.json"
    salida.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    print("=" * 72)
    print(f"BANCO DE PRUEBAS contra {res['motor']}   (cc = {CC:.3f})")
    print("=" * 72)
    for f in filas:
        marca = {True: "coincide", False: "DISCREPA", None: "error   "}[f.get("coincide")]
        esp = "visible" if f["esperado"] else "tapado "
        obt = ("visible" if f["gdal"] else "tapado ") if f["gdal"] is not None else "  -    "
        print(f"  {marca}  esperado={esp}  gdal={obt}  {f['caso'][:46]}")
        if f.get("nota"):
            print(f"            {f['nota'][:66]}")
    print(f"\ncoinciden {ok}/{len(filas)} | discrepan {mal} | errores {err}")
    print(f"\nGuardado: {salida.relative_to(RAIZ)}")


def _geometria_del_caso(fn):
    """Extrae (dem,res,c0,r0,c1,r1,h_obs,h_tgt) interceptando line_of_sight."""
    import los_engine
    capturado = {}
    original = los_engine.line_of_sight

    def espia(dem, res_x, res_y, c0, r0, c1, r1, h_obs=1.7, h_tgt=3.0, **kw):
        capturado.update(dem=dem, res=res_x, c0=c0, r0=r0, c1=c1, r1=r1,
                         h_obs=h_obs, h_tgt=h_tgt)
        return original(dem, res_x, res_y, c0, r0, c1, r1,
                        h_obs=h_obs, h_tgt=h_tgt, **kw)

    los_engine.line_of_sight = espia
    suite.line_of_sight = espia
    try:
        fn(None)
    finally:
        los_engine.line_of_sight = original
        suite.line_of_sight = original
    if not capturado:
        return None
    c = capturado
    return (c["dem"], c["res"], c["c0"], c["r0"], c["c1"], c["r1"],
            c["h_obs"], c["h_tgt"])


if __name__ == "__main__":
    main()
