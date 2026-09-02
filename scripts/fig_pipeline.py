# -*- coding: utf-8 -*-
"""
Figura del pipeline, en clave minimalista: dos lineas de metro que convergen.

No hay cajas, sombras ni rellenos. La estructura la dan una linea vertical por
carril con una parada por etapa, la jerarquia tipografica (negrita para el que,
gris para el como) y el blanco. Un solo acento de color: el rojo de los
defectos, que es el corazon semantico del articulo. Las paradas 1-3 son anillos
huecos; la 4 —el veredicto— es el unico nodo lleno: se llega. Los dos railes
doblan y confluyen en un eje central que atraviesa los diagnosticos y muere en
la regla final, separada por un filete.

Formato: lienzo a los 155 mm reales de impresion, PNG a 300 ppp mas SVG y PDF
vectoriales para la revista.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

TINTA = "#111827"
GRIS = "#6b7280"
SUAVE = "#9ca3af"
RAIL = "#c7cdd6"
ROJO = "#b91c1c"

FS_TIT = 9.4
FS_TXT = 7.3
INTERL = 0.0315


def parada(ax, x, y, llena=False):
    ax.scatter([x], [y], s=30, facecolor=(TINTA if llena else "#ffffff"),
               edgecolor=TINTA, linewidth=1.1, zorder=5)


def etapa(ax, x_rail, y, titulo, lineas, llena=False, tit_color=TINTA):
    parada(ax, x_rail, y, llena)
    tx = x_rail + 0.030
    ax.text(tx, y + 0.012, titulo, ha="left", va="top", fontsize=FS_TIT,
            fontweight="bold", color=tit_color)
    for i, (txt, color) in enumerate(lineas):
        ax.text(tx, y - 0.030 - INTERL * i, txt, ha="left", va="top",
                fontsize=FS_TXT, color=color)


def dibujar(base):
    fig = plt.figure(figsize=(6.10, 4.55))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.rcParams["font.family"] = "Arial"

    XL, XR = 0.060, 0.560   # los dos railes
    TX = 0.030               # sangria del texto respecto al rail

    # ---- cabeceras de carril ------------------------------------------------
    for x, fuerte, resto in ((XL, "ENGINE LEVEL", "is the geometry right?"),
                             (XR, "DESIGN LEVEL", "is the inference right?")):
        ax.text(x + TX, 0.965, fuerte, ha="left", va="top", fontsize=8.2,
                fontweight="bold", color=TINTA)
        ax.text(x + TX, 0.932, resto, ha="left", va="top", fontsize=7.3,
                color=SUAVE, style="italic")

    # ---- railes: verticales, doblan y confluyen -----------------------------
    Y1, Y2, Y3, Y4 = 0.855, 0.680, 0.490, 0.330
    Y_DOBLA = 0.235
    for x in (XL, XR):
        ax.plot([x, x], [Y1, Y_DOBLA], color=RAIL, lw=1.2,
                solid_capstyle="round", zorder=1)
        ax.plot([x, 0.5], [Y_DOBLA, Y_DOBLA], color=RAIL, lw=1.2,
                solid_capstyle="round", zorder=1)
    ax.add_patch(FancyArrowPatch((0.5, Y_DOBLA), (0.5, 0.075),
                                 arrowstyle="-|>", mutation_scale=8,
                                 color=RAIL, lw=1.2, shrinkA=0, shrinkB=0,
                                 zorder=1))

    # ---- carril del motor ---------------------------------------------------
    etapa(ax, XL, Y1, "Line-of-sight engine",
          [("profile sampling · curvature + refraction", GRIS),
           ("5 switchable defects, injected one at a time", ROJO)])
    etapa(ax, XL, Y2, "Benchmark",
          [("15 terrain cases, expectations derived", GRIS),
           ("from the critical distance, not intuition", GRIS),
           ("4 behavioural properties on random terrain", GRIS)])
    etapa(ax, XL, Y3, "Mutation analysis",
          [("the whole benchmark, run against", GRIS),
           ("each deliberately broken engine", GRIS)])
    etapa(ax, XL, Y4, "4 defects killed · 1 equivalent",
          [("equivalence proven by a paired", GRIS),
           ("sweep, not assumed", GRIS)], llena=True)

    # ---- carril del diseno --------------------------------------------------
    etapa(ax, XR, Y1, "Synthetic landscape",
          [("anisotropic ridges · a lake flooded to a", GRIS),
           ("constant, exactly as real DEMs do", GRIS)])
    etapa(ax, XR, Y2, "Ground truth by construction",
          [("S0 exchangeable → p exactly uniform", GRIS),
           ("S1 best of K → known theoretical", GRIS),
           ("power, ceiling 85 %", GRIS)])
    etapa(ax, XR, Y3, "Paired contrasts",
          [("correct · water unmasked · tight crop", GRIS),
           ("same data — only the defect differs", GRIS)])
    etapa(ax, XR, Y4, "Calibration · power · mechanism",
          [("each defect measured against an", GRIS),
           ("exact expectation, not an assumption", GRIS)], llena=True)

    # ---- diagnosticos, sobre el eje central ---------------------------------
    ax.text(0.5, 0.192, "D I A G N O S T I C S   ·   A N Y   R E A L   S T U D Y",
            ha="center", va="top", fontsize=6.4, color=SUAVE)
    ax.text(0.5, 0.158,
            "D1  null placements touching water = 0        "
            "D2  orientation coverage = 100 %",
            ha="center", va="top", fontsize=7.6, color=TINTA)

    # ---- la regla final, tras un filete -------------------------------------
    ax.plot([0.18, 0.82], [0.062, 0.062], color=RAIL, lw=0.8)
    ax.text(0.5, 0.038,
            "Only a validated engine and a diagnosed design touch real terrain.",
            ha="center", va="top", fontsize=8.6, fontweight="bold",
            color=TINTA)

    fig.savefig(os.path.join(base, "fig_pipeline.png"), dpi=300,
                bbox_inches="tight")
    fig.savefig(os.path.join(base, "fig_pipeline.svg"), bbox_inches="tight")
    fig.savefig(os.path.join(base, "fig_pipeline.pdf"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "figuras")
    dibujar(base)
    print("fig_pipeline v4 minimalista: PNG 300 ppp + SVG y PDF")
