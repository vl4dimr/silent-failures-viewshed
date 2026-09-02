# -*- coding: utf-8 -*-
"""
Las tres figuras del articulo, a 300 ppp y con todo calculado en el momento.

Figura 1  La anatomia del fallo silencioso: el mismo par de puntos evaluado por
          el motor correcto y por dos averiados. Ninguna version parece rota;
          esa es la tesis en una imagen.
Figura 2  El laboratorio: un paisaje sintetico con su lago, la nube observada,
          colocaciones nulas fantasma, y el recorte ajustado con las
          orientaciones que excluye.
Figura 3  Las consecuencias: calibracion en S0 (ECDF de los p), potencia en S1,
          y el mecanismo del sesgo del recorte frente al grano del terreno.

Salida: results/figuras/fig_anatomia.png, fig_laboratorio.png, fig_consecuencias.png
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from los_engine import line_of_sight
from suite import RES as RES1D, con_barrera, rugoso
from terrain_lab import (MARGEN_BORDE, _gira, colocacion_S0, forma_alargada,
                        intento_colocacion, paisaje, region_ajustada,
                        cobertura_orientaciones)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
FIG = os.path.join(RES, "figuras")

# El sistema visual de la figura 1 (pipeline), aplicado a los graficos de datos:
# tinta y grises para la estructura, azul para lo corregido/el agua como
# procedimiento, rojo como unico acento semantico (defectos, bloqueos, exclusiones).
# Los lienzos miden lo que mediran impresos: los cuerpos nominales son reales.
plt.rcParams.update({
    "font.family": "Arial", "font.size": 7.5,
    "axes.linewidth": 0.6, "axes.edgecolor": "#c7cdd6",
    "xtick.color": "#6b7280", "ytick.color": "#6b7280",
    "axes.labelcolor": "#374151", "text.color": "#111827",
})

C_TERRENO = "#a8a29e"
C_TERRENO_L = "#e7e5e4"
C_CORR = "#2b5da8"
C_VISTA = "#111827"
C_MAL = "#b91c1c"
C_OK = "#475569"
C_AGUA = "#c9d8e8"


# ------------------------------------------------------------------- figura 1
def ondulado(n=700, cota=3810.0, sd=6.0, sigma=25.0, semilla=0):
    """Llanura con ondulaciones suaves de unos metros, como una ribera.

    El defecto de curvatura solo decide cuando el relieve que hay en juego es
    del orden del abultamiento terrestre —unos 8 m a 20 km—. En montana lo
    tapan cientos de metros de roca; en una llanura costera decide el, y por
    eso es alli donde el error pasa inadvertido con mas facilidad.
    """
    rng = np.random.default_rng(semilla)
    ruido = rng.normal(0, 1, n)
    fx = np.fft.rfftfreq(n)
    filtro = np.exp(-2.0 * (math.pi ** 2) * (sigma ** 2) * fx ** 2)
    suave = np.fft.irfft(np.fft.rfft(ruido) * filtro, n)
    suave *= sd / suave.std()
    return np.tile((cota + suave).astype(np.float32), (3, 1))


def buscar_par_curvatura():
    """Un par bloqueado por el motor correcto y despejado por el averiado.

    Se busca sobre llanuras onduladas: el relieve que decide debe ser modesto,
    porque cuanto mas discreto el obstaculo, mas verosimil resulta la
    respuesta equivocada.
    """
    for s in range(200):
        dem = ondulado(semilla=s)
        for c1 in (699, 640, 580, 520):
            ok = line_of_sight(dem, RES1D, RES1D, 0, 1, c1, 1)
            mal = line_of_sight(dem, RES1D, RES1D, 0, 1, c1, 1, defecto="curvatura_restada")
            if (not ok) and mal:
                return dem, c1, s
    raise RuntimeError("sin ejemplo")


def perfil(ax, dem, c1, defecto, titulo, veredicto, color_v):
    _, pr = line_of_sight(dem, RES1D, RES1D, 0, 1, c1, 1, defecto=defecto,
                          return_profile=True)
    km = pr["d"] / 1000.0
    z0 = pr["z"].min() - 15
    ax.fill_between(km, z0, pr["z"], color=C_TERRENO_L, lw=0)
    ax.plot(km, pr["z"], color=C_TERRENO, lw=0.7, label="terrain")
    ax.plot(km, pr["z_corr"], color=C_CORR, lw=0.9,
            label="terrain, curvature-corrected")
    ax.plot(km, pr["vista"], color=C_VISTA, lw=0.9, ls="--", label="line of sight")
    # la franja donde el terreno corregido supera la visual
    exceso = pr["z_corr"] > pr["vista"]
    exceso[0] = exceso[-1] = False
    if exceso.any():
        ax.fill_between(km, pr["vista"], pr["z_corr"], where=exceso,
                        color=C_MAL, alpha=0.55, lw=0)
        # cuanto sobresale el relieve que decide: la sutileza es el argumento
        i = int(np.argmax(np.where(exceso, pr["z_corr"] - pr["vista"], -1)))
        ax.annotate("obstruction: %.1f m above the line" % (pr["z_corr"][i] - pr["vista"][i]),
                    (km[i], pr["z_corr"][i]), xytext=(12, 26),
                    textcoords="offset points", fontsize=7.5, color=C_MAL,
                    arrowprops=dict(arrowstyle="-", color=C_MAL, lw=0.7))
    ax.set_title(titulo, fontsize=8.5, loc="left")
    ax.text(0.985, 0.06, veredicto, transform=ax.transAxes, ha="right",
            fontsize=8.5, fontweight="bold", color=color_v)
    ax.set_ylim(z0, pr["z"].max() + 40)
    ax.margins(x=0)


def figura1():
    dem, c1, sem = buscar_par_curvatura()
    fig, axs = plt.subplots(2, 2, figsize=(6.10, 4.9))

    perfil(axs[0, 0], dem, c1, None,
           "(a) Correct engine — %.1f km" % (c1 * RES1D / 1000),
           "BLOCKED", C_MAL)
    perfil(axs[0, 1], dem, c1, "curvatura_restada",
           "(b) Curvature subtracted, same pair",
           "CLEAR", C_OK)

    # (c) muestreo grueso: la barrera de una celda queda entre dos muestras
    demb = con_barrera(n=100, altura=80.0, ancho=1)
    _, prb = line_of_sight(demb, RES1D, RES1D, 0, 1, 99, 1, return_profile=True)
    _, prg = line_of_sight(demb, RES1D, RES1D, 0, 1, 99, 1, defecto="muestreo_grueso",
                           return_profile=True)
    ax = axs[1, 0]
    kmb = prb["d"] / 1000.0
    z0 = prb["z"].min() - 8
    ax.fill_between(kmb, z0, prb["z"], color=C_TERRENO_L, lw=0)
    ax.plot(kmb, prb["z"], color=C_TERRENO, lw=0.7)
    ax.plot(prg["d"] / 1000.0, prg["z"], "o", ms=4, color=C_MAL, mfc="white",
            label="coarse samples (10)")
    ax.plot(kmb, prb["vista"], color=C_VISTA, lw=0.9, ls="--")
    ax.set_title("(c) Coarse sampling misses an 80 m barrier",
                 fontsize=8.5, loc="left")
    ax.text(0.985, 0.06, "CLEAR", transform=ax.transAxes, ha="right",
            fontsize=8.5, fontweight="bold", color=C_OK)
    ax.legend(loc="upper left", frameon=False, fontsize=7.5)
    ax.margins(x=0)

    # (d) el mismo par de (a) recortado a corta distancia: todo motor coincide
    c_corto = int(c1 * 0.15)
    perfil(axs[1, 1], dem, c_corto, None,
           "(d) At %.1f km every variant agrees" % (c_corto * RES1D / 1000),
           "CLEAR", C_OK)

    axs[0, 0].legend(loc="upper left", frameon=False, fontsize=7.5)
    for ax in axs.flat:
        ax.set_xlabel("distance (km)", fontsize=8)
        ax.set_ylabel("elevation (m)", fontsize=8)
    fig.tight_layout(pad=1.1)
    fig.savefig(os.path.join(FIG, "fig_anatomia.png"), dpi=300)
    plt.close(fig)
    meta = {"fig1_semilla": sem, "fig1_km": c1 * RES1D / 1000,
            "fig1_km_corto": c_corto * RES1D / 1000}
    ruta = os.path.join(FIG, "meta.json")
    previo = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    previo.update(meta)
    json.dump(previo, open(ruta, "w", encoding="utf-8"), indent=2)
    print("figura 1: semilla del ejemplo %d, par a %.1f km" % (sem, c1 * RES1D / 1000))


# ------------------------------------------------------------------- figura 2
def sombreado(dem, res=30.0, az=315.0, alt=45.0):
    gy, gx = np.gradient(dem, res)
    az, alt = math.radians(az), math.radians(alt)
    pend = np.arctan(np.hypot(gx, gy))
    orient = np.arctan2(-gx, gy)
    s = (math.sin(alt) * np.cos(pend)
         + math.cos(alt) * np.sin(pend) * np.cos(az - orient))
    return np.clip(s, 0, 1)


def figura2():
    dem, agua, theta = paisaje(semilla=7)
    rng = np.random.default_rng(41)
    dc, dr = forma_alargada(rng)
    cc, fr, ang = colocacion_S0(dem, agua, dc, dr, rng)
    reg = region_ajustada(cc, fr, dem, 25)
    cob_full = cobertura_orientaciones(dem, dc, dr)
    cob_tight = cobertura_orientaciones(dem, dc, dr, reg)

    fig = plt.figure(figsize=(6.95, 4.9))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1], hspace=0.42, wspace=0.16)

    # (a) el paisaje
    ax = fig.add_subplot(gs[:, 0])
    sh = sombreado(dem)
    ax.imshow(sh, cmap="gray", vmin=0, vmax=1, alpha=0.9)
    ax.imshow(np.ma.masked_where(~agua, np.ones_like(dem)), cmap=
              matplotlib.colors.ListedColormap([C_AGUA]), alpha=0.95)
    # colocaciones nulas fantasma
    rng2 = np.random.default_rng(5)
    fantasmas = 0
    while fantasmas < 3:
        col = intento_colocacion(dem, agua, dc, dr, rng2)
        if col is None:
            continue
        ax.plot(col[0], col[1], ".", ms=2.2, color="#9ca3af", alpha=0.85)
        fantasmas += 1
    ax.plot(cc, fr, ".", ms=3.2, color=C_MAL)
    rmin, rmax, cmin, cmax = reg
    ax.add_patch(Rectangle((cmin, rmin), cmax - cmin, rmax - rmin,
                           fill=False, ec=C_MAL, lw=1.1, ls="--"))
    ax.text(cmin, rmin - 6, "tightly cropped sampling region", fontsize=7.5,
            color=C_MAL, bbox=dict(facecolor="#ffffff", edgecolor="none",
                                   pad=1.6, alpha=0.9))
    ax.set_title("(a) Synthetic landscape: lake, observed cloud (red),\n"
                 "null placements (grey), and the crop defect (dashed)",
                 fontsize=8.5, loc="left")
    ax.set_xticks([]); ax.set_yticks([])
    # barra de escala: 5 km son 167 celdas de 30 m
    h, w = dem.shape
    x0, y0, celdas = w * 0.05, h * 0.95, 5000.0 / 30.0
    ax.plot([x0, x0 + celdas], [y0, y0], color="#111827", lw=2.2,
            solid_capstyle="butt")
    ax.text(x0 + celdas / 2, y0 - 7, "5 km", ha="center", fontsize=7.5,
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=1.4, alpha=0.9))

    # (b) cobertura de orientaciones, region completa
    for fila, (region, cob, tit) in enumerate((
            (None, cob_full, "(b) Orientation coverage, full region: %.0f %%" % (100 * cob_full)),
            (reg, cob_tight, "(c) Tightly cropped region: %.0f %%" % (100 * cob_tight)))):
        ax = fig.add_subplot(gs[fila, 1])
        caben = []
        for k in range(360):
            a = 2 * math.pi * k / 360
            rc, rr = _gira(dc, dr, a)
            if region is None:
                h, w = dem.shape
                rmn, rmx, cmn, cmx = MARGEN_BORDE, h - 1 - MARGEN_BORDE, MARGEN_BORDE, w - 1 - MARGEN_BORDE
            else:
                rmn, rmx, cmn, cmx = region
            caben.append(1 if (cmn - rc.min() < cmx - rc.max()
                               and rmn - rr.min() < rmx - rr.max()) else 0)
        caben = np.array(caben)
        ax.bar(np.arange(360), caben, width=1.0,
               color=np.where(caben > 0, C_OK, C_MAL), lw=0)
        ax.set_ylim(0, 1.25)
        ax.set_yticks([0.5])
        ax.set_yticklabels(["fits"], fontsize=7)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, 360)
        ax.set_xticks([0, 90, 180, 270, 360])
        ax.set_xlabel("orientation of the null placement (degrees)", fontsize=7.5)
        ax.set_title(tit, fontsize=8.5, loc="left")
    fig.savefig(os.path.join(FIG, "fig_laboratorio.png"), dpi=300,
                bbox_inches="tight")
    plt.close(fig)
    ruta = os.path.join(FIG, "meta.json")
    previo = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    previo.update({"fig2_cobertura_completa": cob_full, "fig2_cobertura_ajustada": cob_tight})
    json.dump(previo, open(ruta, "w", encoding="utf-8"), indent=2)
    print("figura 2: cobertura completa %.2f, ajustada %.2f" % (cob_full, cob_tight))


# ------------------------------------------------------------------- figura 3
def figura3():
    cal = json.load(open(os.path.join(RES, "calibracion.json"), encoding="utf-8"))
    reps, res = cal["replicas"], cal["resumen"]
    PROCS = [("correcto", "correct", "#475569"),
             ("agua", "water unmasked", "#2b5da8"),
             ("recorte", "tight crop", "#b91c1c")]

    fig, axs = plt.subplots(1, 3, figsize=(6.10, 2.5))

    # (a) calibracion: ECDF de p en S0
    ax = axs[0]
    ax.plot([0, 1], [0, 1], color="#999999", lw=0.8, ls=":", zorder=1)
    for clave, eti, color in PROCS:
        ps = np.sort([r["S0"][clave]["p"] for r in reps])
        ax.step(np.concatenate([[0], ps]),
                np.concatenate([[0], np.arange(1, len(ps) + 1) / len(ps)]),
                where="post", color=color, lw=1.2, label=eti)
    ax.set_xlabel("p-value under no effect (S0)")
    ax.set_ylabel("empirical CDF")
    ax.set_title("(a) Calibration: p should be uniform", fontsize=8.5, loc="left")
    ax.legend(frameon=False, fontsize=7.0, loc="upper left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # (b) potencia: z en S1 por procedimiento
    ax = axs[1]
    rng = np.random.default_rng(3)
    etiquetas = []
    for i, (clave, eti, color) in enumerate(PROCS):
        zs = np.array([r["S1"][clave]["z"] for r in reps])
        xj = i + rng.uniform(-0.13, 0.13, len(zs))
        ax.plot(xj, zs, ".", ms=3.2, color=color, alpha=0.7)
        ax.hlines(np.mean(zs), i - 0.22, i + 0.22, color=color, lw=1.6)
        corta = {"correct": "correct", "water unmasked": "water",
                 "tight crop": "crop"}[eti]
        # la potencia va bajo cada columna, no flotando sobre los puntos
        etiquetas.append("%s\n%.0f %%"
                         % (corta, 100 * res["S1"][clave]["rechazo"]))
    ax.axhline(0, color="#c7cdd6", lw=0.6, ls=":")
    ax.set_xticks(range(len(PROCS)))
    ax.set_xticklabels(etiquetas, fontsize=7.0)
    ax.set_xlim(-0.5, len(PROCS) - 0.5)
    ax.set_ylabel("z under a real effect (S1)")
    ax.set_title("(b) Power (ceiling %.0f %%)"
                 % (100 * res["potencia_teorica_S1_correcto"]),
                 fontsize=8.5, loc="left")

    # (c) mecanismo del recorte
    ax = axs[2]
    des = [r["S0"]["desalineacion_grados"] for r in reps]
    dz = [r["S0"]["recorte"]["z"] - r["S0"]["correcto"]["z"] for r in reps]
    ax.axhline(0, color="#999999", lw=0.6, ls=":")
    ax.plot(des, dz, "o", ms=3.6, color="#b91c1c", alpha=0.75, mec="none")
    m = res["mecanismo_recorte"]
    ax.set_xlabel("misalignment with terrain grain (°)")
    ax.set_ylabel(r"$\Delta z$ (tight crop $-$ correct)")
    p_rho = ("p < 0.001" if m["p_spearman"] < 0.001
             else "p = %.3f" % m["p_spearman"])
    ax.set_title("(c) Crop bias vs. terrain grain", fontsize=8.5, loc="left")
    # la correlacion, dentro del panel y sobre hueco limpio
    ax.text(0.97, 0.95, r"$\rho_s$ = %+.2f, %s"
            % (m["spearman_desalineacion"], p_rho),
            transform=ax.transAxes, ha="right", va="top", fontsize=7.2,
            color="#374151")

    fig.tight_layout(pad=1.1)
    fig.savefig(os.path.join(FIG, "fig_consecuencias.png"), dpi=300)
    plt.close(fig)
    print("figura 3 generada")


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    figura1()
    figura2()
    if os.path.exists(os.path.join(RES, "calibracion.json")):
        figura3()
    else:
        print("figura 3 pendiente: aun no existe calibracion.json")
