# -*- coding: utf-8 -*-
"""Corre el banco de pruebas contra GRASS r.viewshed.

GRASS es, junto con GDAL, el motor de visibilidad que la arqueologia usa por
debajo de QGIS. Interesa por dos motivos: es una implementacion independiente
de la de GDAL —lo que permite medir la discrepancia que observo Fisher (1993)
en lugar de solo citarla— y porque su tratamiento de la curvatura terrestre
NO esta activado por defecto: hay que pedirlo con la bandera -c.

Salida: results/grass_viewshed.json
Uso:    python scripts/p08_grass_viewshed.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import suite                                    # noqa: E402
from los_engine import K_REFRACTION             # noqa: E402
from p07_motores_reales import escribir_geotiff, _geometria_del_caso  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
QGIS = Path(r"C:\Program Files\QGIS 3.44.13")
GRASS = QGIS / "bin" / "grass85.bat"

ENTORNO = dict(os.environ)
ENTORNO["PATH"] = str(QGIS / "bin") + os.pathsep + ENTORNO.get("PATH", "")
ENTORNO["GDAL_DATA"] = str(QGIS / "share" / "gdal")
ENTORNO["PROJ_LIB"] = str(QGIS / "share" / "proj")


def grass_viewshed(dem, res, c0, r0, c1, r1, h_obs, h_tgt, base: Path,
                   curvatura=True):
    """Veredicto de r.viewshed. Con curvatura=False se usa su valor de fabrica."""
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

    # r.viewshed escribe el mapa; se exporta la celda del objetivo con r.what
    orden = (
        f"r.in.gdal input={tif} output=dem --overwrite --quiet && "
        f"g.region raster=dem --quiet && "
        f"r.viewshed input=dem output=vs coordinates={ox},{oy} "
        f"observer_elevation={h_obs} target_elevation={h_tgt} "
        f"memory=2000 --overwrite --quiet"
        + (f" -c refraction_coeff={K_REFRACTION}" if curvatura else "")
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
        return None, ((r.stderr or r.stdout) or "sin salida")[-200:]

    txt = salida_txt.read_text(encoding="utf-8", errors="ignore").strip()
    # formato: este|norte||valor   (vacio o '*' = no visible / nulo)
    campos = txt.split("|")
    valor = campos[-1].strip() if campos else ""
    salida_txt.unlink(missing_ok=True)
    shutil.rmtree(trabajo, ignore_errors=True)
    tif.unlink(missing_ok=True)

    if valor in ("", "*"):
        return False, None       # celda nula: fuera del viewshed
    try:
        return float(valor) >= 0.0, None
    except ValueError:
        return None, f"valor no interpretable: {valor!r}"


def main():
    if not GRASS.exists():
        sys.exit(f"no se encontro GRASS en {GRASS}")

    filas, err = [], 0
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        for nombre, fn, esperado in suite.casos():
            geo = _geometria_del_caso(fn)
            if geo is None:
                continue
            dem, res, c0, r0, c1, r1, h_obs, h_tgt = geo
            con, e1 = grass_viewshed(dem, res, c0, r0, c1, r1, h_obs, h_tgt,
                                     base, curvatura=True)
            sin, _ = grass_viewshed(dem, res, c0, r0, c1, r1, h_obs, h_tgt,
                                    base, curvatura=False)
            if con is None:
                err += 1
            filas.append(dict(
                caso=nombre, esperado=bool(esperado),
                con_curvatura=con,
                coincide=(con == bool(esperado)) if con is not None else None,
                de_fabrica=sin,
                coincide_fabrica=(sin == bool(esperado)) if sin is not None else None,
                nota=e1))

    ok = sum(1 for f in filas if f.get("coincide") is True)
    okf = sum(1 for f in filas if f.get("coincide_fabrica") is True)
    res = dict(motor="GRASS r.viewshed 8.5.0 (QGIS 3.44.13)",
               nota_curvatura="r.viewshed NO aplica curvatura salvo que se pase -c",
               casos=len(filas),
               con_curvatura=dict(coinciden=ok, discrepan=len(filas) - ok - err),
               de_fabrica=dict(coinciden=okf, discrepan=len(filas) - okf),
               errores=err, detalle=filas)
    (RAIZ / "results" / "grass_viewshed.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 74)
    print("BANCO DE PRUEBAS contra GRASS r.viewshed 8.5.0")
    print("=" * 74)
    print(f"{'con -c':>8} {'fabrica':>9}   caso")
    for f in filas:
        m1 = {True: "   ok   ", False: " FALLA  ", None: " error  "}[f.get("coincide")]
        m2 = {True: "   ok   ", False: " FALLA  ", None: " error  "}[f.get("coincide_fabrica")]
        print(f"{m1} {m2}   {f['caso'][:52]}")
        if f.get("nota"):
            print(f"          {f['nota'][:64]}")
    print(f"\n  con curvatura (-c)      : {ok}/{len(filas)}")
    print(f"  de fabrica (sin -c)     : {okf}/{len(filas)}")
    print(f"  errores                 : {err}")


if __name__ == "__main__":
    main()
