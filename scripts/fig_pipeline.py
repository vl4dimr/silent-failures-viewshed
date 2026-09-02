# -*- coding: utf-8 -*-
"""
Figura del pipeline: la arquitectura de los dos instrumentos en un diagrama.

Dos decisiones de formato importan tanto como el dibujo. El lienzo mide lo que
medira impreso (155 mm de ancho), de modo que los cuerpos tipograficos nominales
son los reales: nada baja de 6 pt en papel. Y ademas del PNG a 300 ppp se
exportan SVG y PDF vectoriales, porque la revista pide el original vectorial de
los dibujos de linea.

El lenguaje visual es el del diseno editorial corporativo estadounidense: azul
marino y pizarra, tarjetas blancas con lomo de acento a la izquierda, barras de
carril solidas con versales blancas, contraste alto y nada de ornamento. Cada
color codifica una cosa: azul para el proceso, rojo para los defectos, verde
para los veredictos, y el marino cierra la regla final.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

NAVY = "#16294a"
NAVY_TXT = "#0f1c33"
AZUL = "#2b5da8"
PIZARRA = "#94a3b8"
TXT = "#111827"
TXT2 = "#374151"
ROJO = "#b91c1c"
VERDE = "#15803d"
VERDE_F = "#f0f7f1"
AZUL_F = "#eff4fb"
PANEL = "#f4f6f8"
PANEL_B = "#d8dee6"
CARD = "#ffffff"

FS_T, FS_C = 8.4, 7.1


def caja(ax, x, y, w, h, titulo, cuerpo=None, fc=CARD, ec=PIZARRA, tc=TXT,
         tb=TXT2, lomo=None, lw=0.8, fs_t=FS_T, fs_c=FS_C, radio=0.003):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=%s" % radio,
                                fc=fc, ec=ec, lw=lw))
    if lomo:
        # el lomo de acento: la firma del estilo
        ax.add_patch(Rectangle((x - radio, y - radio), 0.009,
                               h + 2 * radio, fc=lomo, ec="none", zorder=3))
    if cuerpo:
        ax.text(x + w / 2, y + h - 0.012, titulo, ha="center", va="top",
                fontsize=fs_t, fontweight="bold", color=tc)
        ax.text(x + w / 2, y + h - 0.056, cuerpo, ha="center", va="top",
                fontsize=fs_c, color=tb, linespacing=1.5)
    else:
        ax.text(x + w / 2, y + h / 2, titulo, ha="center", va="center",
                fontsize=fs_t, fontweight="bold", color=tc)


def barra_carril(ax, x, y, w, texto):
    ax.add_patch(Rectangle((x, y), w, 0.052, fc=NAVY, ec="none"))
    ax.text(x + w / 2, y + 0.026, texto, ha="center", va="center",
            fontsize=7.9, fontweight="bold", color="#ffffff")


def flecha(ax, x, y0, y1, color="#475569"):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>",
                                 mutation_scale=9, color=color, lw=1.1,
                                 shrinkA=0, shrinkB=0))


def dibujar(base):
    # los ejes ocupan el lienzo entero: el recorte ajustado conserva las
    # 6.10 pulgadas y el PNG sale a 300 ppp reales a 155 mm
    fig = plt.figure(figsize=(6.10, 4.62))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.rcParams["font.family"] = "Arial"

    # ---- paneles y barras de carril ----------------------------------------
    PY, PH = 0.180, 0.805
    for px, rotulo in ((0.012, "ENGINE LEVEL — IS THE GEOMETRY RIGHT?"),
                       (0.518, "DESIGN LEVEL — IS THE INFERENCE RIGHT?")):
        ax.add_patch(FancyBboxPatch((px, PY), 0.47, PH,
                                    boxstyle="round,pad=0.005",
                                    fc=PANEL, ec=PANEL_B, lw=0.8))
        barra_carril(ax, px + 0.012, PY + PH - 0.060, 0.446, rotulo)

    LX, RX, W = 0.036, 0.542, 0.422
    CL, CR = LX + W / 2, RX + W / 2

    # ---- fila 1 -------------------------------------------------------------
    caja(ax, LX, 0.790, W, 0.115, "Line-of-sight engine",
         "profile sampling · curvature + refraction", lomo=AZUL)
    ax.text(LX + W / 2, 0.790 + 0.115 - 0.084,
            "5 switchable defects, injected one at a time",
            ha="center", va="top", fontsize=FS_C, color=ROJO,
            fontweight="bold")
    caja(ax, RX, 0.790, W, 0.115, "Synthetic landscape",
         "anisotropic ridges · lake flooded to a constant", lomo=AZUL)
    for x0 in (CL, CR):
        flecha(ax, x0, 0.787, 0.755)

    # ---- fila 2 -------------------------------------------------------------
    caja(ax, LX, 0.583, W, 0.160, "Benchmark",
         "15 terrain cases, expectations derived\n"
         "(critical distance, not intuition)\n"
         "4 behavioural properties on random terrain", lomo=AZUL)
    caja(ax, RX, 0.583, W, 0.160, "Ground truth by construction",
         "S0 exchangeable → p exactly uniform\n"
         "S1 best of K placements → known power\n"
         "(theoretical ceiling 85 %)", lomo=AZUL)
    for x0 in (CL, CR):
        flecha(ax, x0, 0.580, 0.548)

    # ---- fila 3 -------------------------------------------------------------
    caja(ax, LX, 0.428, W, 0.110, "Mutation analysis",
         "run the whole benchmark against\neach deliberately broken engine",
         lomo=ROJO)
    caja(ax, RX, 0.428, W, 0.110, "Paired contrasts",
         "correct · water unmasked · tight crop\nsame data; only the defect differs",
         lomo=ROJO)
    for x0 in (CL, CR):
        flecha(ax, x0, 0.425, 0.390)

    # ---- fila 4: veredictos -------------------------------------------------
    caja(ax, LX, 0.243, W, 0.135, "4 defects killed · 1 equivalent",
         "equivalence proven by paired sweep,\nnot assumed",
         fc=VERDE_F, ec=VERDE, tc="#14532d", tb="#2f6b40", lomo=VERDE)
    caja(ax, RX, 0.243, W, 0.135, "Calibration · power · mechanism",
         "what each defect does to inference,\nmeasured against an exact expectation",
         fc=VERDE_F, ec=VERDE, tc="#14532d", tb="#2f6b40", lomo=VERDE)
    for x0 in (CL, CR):
        flecha(ax, x0, 0.240, 0.198)

    # ---- diagnosticos y desembocadura --------------------------------------
    caja(ax, 0.120, 0.098, 0.760, 0.096, "Diagnostics for any real study",
         "D1: null placements touching water = 0"
         "        D2: orientation coverage = 100 %",
         fc=AZUL_F, ec=AZUL, tc=NAVY_TXT, tb="#274e86", lomo=AZUL)
    flecha(ax, 0.5, 0.095, 0.080)

    # la regla final: barra maciza, blanco sobre marino
    ax.add_patch(FancyBboxPatch((0.110, 0.016), 0.780, 0.058,
                                boxstyle="round,pad=0.003",
                                fc=NAVY, ec="none"))
    ax.text(0.5, 0.045,
            "Only a validated engine and a diagnosed design touch real terrain",
            ha="center", va="center", fontsize=8.1, fontweight="bold",
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
    print("fig_pipeline: PNG a 300 ppp + SVG y PDF vectoriales")
