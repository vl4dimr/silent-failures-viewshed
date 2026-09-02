# -*- coding: utf-8 -*-
"""
Figura del pipeline: la arquitectura de los dos instrumentos en un diagrama.

Reglas de composicion, en este orden de importancia. Texto alineado a la
izquierda dentro de las tarjetas: el centrado universal es la firma del
diagrama hecho a maquina. Ninguna caja dentro de otra: las columnas las
definen las barras de carril y el blanco, no un contenedor. Bordes casi
invisibles: la estructura la dan el lomo de acento, la sombra tenue y el
espacio. Etapas numeradas con chip: 1-4, las mismas en ambos carriles, porque
los dos instrumentos avanzan en paralelo. Y una sola familia (Arial) con
jerarquia por peso y tamano, no por adorno.

Formato: el lienzo mide los 155 mm a los que ira impreso —los cuerpos
nominales son los reales— y se exporta PNG a 300 ppp mas SVG y PDF
vectoriales, que la revista pide para dibujos de linea.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

NAVY = "#16294a"
AZUL = "#2b5da8"
ROJO = "#b91c1c"
VERDE = "#15803d"
TITULO = "#111827"
CUERPO = "#4b5563"
BORDE = "#e2e8f0"
SOMBRA = "#d9dde3"
LINEA = "#64748b"


def sombra(ax, x, y, w, h):
    ax.add_patch(FancyBboxPatch((x + 0.004, y - 0.006), w, h,
                                boxstyle="round,pad=0.004",
                                fc=SOMBRA, ec="none", zorder=1))


def tarjeta(ax, x, y, w, h, num, titulo, lineas, lomo=AZUL,
            titulo_color=TITULO):
    """Tarjeta blanca con lomo, chip numerado y texto a la izquierda."""
    sombra(ax, x, y, w, h)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004",
                                fc="#ffffff", ec=BORDE, lw=0.7, zorder=2))
    ax.add_patch(Rectangle((x - 0.004, y - 0.004), 0.0065, h + 0.008,
                           fc=lomo, ec="none", zorder=3))
    tx = x + 0.030
    ty = y + h - 0.016
    if num:
        ax.add_patch(FancyBboxPatch((tx - 0.002, ty - 0.030), 0.030, 0.032,
                                    boxstyle="round,pad=0.002",
                                    fc=NAVY, ec="none", zorder=4))
        ax.text(tx + 0.013, ty - 0.013, num, ha="center", va="center",
                fontsize=7.4, fontweight="bold", color="#ffffff", zorder=5)
        ax.text(tx + 0.040, ty, titulo, ha="left", va="top",
                fontsize=8.8, fontweight="bold", color=titulo_color, zorder=4)
    else:
        ax.text(tx, ty, titulo, ha="left", va="top",
                fontsize=8.8, fontweight="bold", color=titulo_color, zorder=4)
    for i, (txt, color) in enumerate(lineas):
        ax.text(tx, ty - 0.048 - 0.033 * i, txt, ha="left", va="top",
                fontsize=7.2, color=color, zorder=4)


def barra(ax, x, y, w, texto):
    ax.add_patch(Rectangle((x, y), w, 0.050, fc=NAVY, ec="none"))
    ax.text(x + 0.016, y + 0.025, texto, ha="left", va="center",
            fontsize=7.8, fontweight="bold", color="#ffffff")


def conector(ax, x, y0, y1):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>",
                                 mutation_scale=7, color=LINEA, lw=0.9,
                                 shrinkA=0, shrinkB=0))


def dibujar(base):
    fig = plt.figure(figsize=(6.10, 4.90))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.rcParams["font.family"] = "Arial"

    LX, RX, W = 0.030, 0.535, 0.435
    CL, CR = LX + W / 2, RX + W / 2

    # ---- barras de carril ---------------------------------------------------
    barra(ax, LX, 0.936, W, "ENGINE LEVEL — IS THE GEOMETRY RIGHT?")
    barra(ax, RX, 0.936, W, "DESIGN LEVEL — IS THE INFERENCE RIGHT?")

    # ---- etapa 1 ------------------------------------------------------------
    tarjeta(ax, LX, 0.778, W, 0.128, "1", "Line-of-sight engine",
            [("profile sampling · curvature + refraction", CUERPO),
             ("5 switchable defects, injected one at a time", ROJO)])
    tarjeta(ax, RX, 0.778, W, 0.128, "1", "Synthetic landscape",
            [("anisotropic ridges · a lake flooded to a", CUERPO),
             ("constant, exactly as real DEMs build lakes", CUERPO)])
    for x0 in (CL, CR):
        conector(ax, x0, 0.772, 0.742)

    # ---- etapa 2 ------------------------------------------------------------
    tarjeta(ax, LX, 0.578, W, 0.160, "2", "Benchmark",
            [("15 terrain cases — expectations derived", CUERPO),
             ("from the critical distance, not intuition", CUERPO),
             ("4 behavioural properties, random terrain", CUERPO)])
    tarjeta(ax, RX, 0.578, W, 0.160, "2", "Ground truth by construction",
            [("S0 exchangeable  →  p exactly uniform", CUERPO),
             ("S1 best of K  →  known theoretical power", CUERPO),
             ("(ceiling 85 %)", CUERPO)])
    for x0 in (CL, CR):
        conector(ax, x0, 0.572, 0.542)

    # ---- etapa 3 ------------------------------------------------------------
    tarjeta(ax, LX, 0.410, W, 0.128, "3", "Mutation analysis",
            [("the whole benchmark, run against each", CUERPO),
             ("deliberately broken engine", CUERPO)], lomo=ROJO)
    tarjeta(ax, RX, 0.410, W, 0.128, "3", "Paired contrasts",
            [("correct · water unmasked · tight crop", CUERPO),
             ("same data — only the defect differs", CUERPO)], lomo=ROJO)
    for x0 in (CL, CR):
        conector(ax, x0, 0.404, 0.374)

    # ---- etapa 4: veredictos ------------------------------------------------
    tarjeta(ax, LX, 0.240, W, 0.130, "4", "4 defects killed · 1 equivalent",
            [("equivalence proven by a paired sweep,", CUERPO),
             ("not assumed", CUERPO)], lomo=VERDE, titulo_color="#14532d")
    tarjeta(ax, RX, 0.240, W, 0.130, "4", "Calibration · power · mechanism",
            [("each defect measured against an exact", CUERPO),
             ("expectation, not an assumption", CUERPO)],
            lomo=VERDE, titulo_color="#14532d")
    for x0 in (CL, CR):
        conector(ax, x0, 0.234, 0.204)

    # ---- diagnosticos -------------------------------------------------------
    DX, DW = 0.115, 0.770
    sombra(ax, DX, 0.106, DW, 0.092)
    ax.add_patch(FancyBboxPatch((DX, 0.106), DW, 0.092,
                                boxstyle="round,pad=0.004",
                                fc="#ffffff", ec=BORDE, lw=0.7, zorder=2))
    ax.add_patch(Rectangle((DX - 0.004, 0.102), 0.0065, 0.100,
                           fc=AZUL, ec="none", zorder=3))
    ax.text(DX + 0.030, 0.180, "Diagnostics for any real study",
            ha="left", va="top", fontsize=8.8, fontweight="bold",
            color=TITULO, zorder=4)
    ax.text(DX + 0.030, 0.134, "D1   null placements touching water = 0",
            ha="left", va="top", fontsize=7.2, color="#274e86", zorder=4)
    ax.text(DX + 0.415, 0.134, "D2   orientation coverage = 100 %",
            ha="left", va="top", fontsize=7.2, color="#274e86", zorder=4)
    conector(ax, 0.5, 0.100, 0.082)

    # ---- la regla final -----------------------------------------------------
    ax.add_patch(Rectangle((DX, 0.020), DW, 0.052, fc=NAVY, ec="none"))
    ax.text(0.5, 0.046,
            "ONLY A VALIDATED ENGINE AND A DIAGNOSED DESIGN TOUCH REAL TERRAIN",
            ha="center", va="center", fontsize=7.6, fontweight="bold",
            color="#ffffff")

    fig.savefig(os.path.join(base, "fig_pipeline.png"), dpi=300,
                bbox_inches="tight")
    fig.savefig(os.path.join(base, "fig_pipeline.svg"), bbox_inches="tight")
    fig.savefig(os.path.join(base, "fig_pipeline.pdf"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "figuras")
    dibujar(base)
    print("fig_pipeline v3: PNG 300 ppp + SVG y PDF vectoriales")
