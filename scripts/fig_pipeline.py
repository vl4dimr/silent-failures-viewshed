# -*- coding: utf-8 -*-
"""
Figura del pipeline: la arquitectura de los dos instrumentos en un diagrama.

Dos decisiones de formato importan tanto como el dibujo. El lienzo mide lo que
medira impreso (155 mm de ancho), de modo que los cuerpos tipograficos nominales
son los reales: nada baja de 6 pt en papel. Y ademas del PNG a 300 ppp se
exportan SVG y PDF vectoriales, porque la revista pide el original vectorial de
los dibujos de linea.

El lenguaje visual es el del resto de figuras: paneles en crema, tarjetas
blancas con borde fino, verde para los veredictos, rojo para los defectos.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

C_PANEL = "#f6f3ec"
C_PANEL_B = "#d8d2c4"
C_CARD = "#ffffff"
C_BORDE = "#55524b"
C_TXT = "#26231f"
C_TXT2 = "#4a463f"
C_MAL = "#b0413e"
C_OK = "#3d7a4a"
C_OK_F = "#eef5ef"
C_DIAG = "#eef3f7"
C_DIAG_B = "#5b7ea8"
C_FIN_F = "#fdf7ec"
C_FIN_B = "#8a6a2f"

FS_T, FS_C = 8.4, 7.1


def caja(ax, x, y, w, h, titulo, cuerpo=None, fc=C_CARD, ec=C_BORDE,
         tc=C_TXT, tb=C_TXT2, lw=0.9, fs_t=FS_T, fs_c=FS_C):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006",
                                fc=fc, ec=ec, lw=lw))
    if cuerpo:
        ax.text(x + w / 2, y + h - 0.012, titulo, ha="center", va="top",
                fontsize=fs_t, fontweight="bold", color=tc)
        ax.text(x + w / 2, y + h - 0.056, cuerpo, ha="center", va="top",
                fontsize=fs_c, color=tb, linespacing=1.5)
    else:
        ax.text(x + w / 2, y + h / 2, titulo, ha="center", va="center",
                fontsize=fs_t, fontweight="bold", color=tc)


def flecha(ax, x, y0, y1, color=C_BORDE):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>",
                                 mutation_scale=9, color=color, lw=1.0,
                                 shrinkA=0, shrinkB=0))


def dibujar(base):
    # los ejes ocupan el lienzo entero: sin margenes, el recorte ajustado
    # conserva las 6.10 pulgadas y el PNG sale a 300 ppp reales a 155 mm
    fig = plt.figure(figsize=(6.10, 4.62))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.rcParams["font.family"] = "Arial"

    # ---- paneles de carril --------------------------------------------------
    PY, PH = 0.180, 0.805
    for px, rotulo in ((0.012, "ENGINE LEVEL — is the geometry right?"),
                       (0.518, "DESIGN LEVEL — is the inference right?")):
        ax.add_patch(FancyBboxPatch((px, PY), 0.47, PH,
                                    boxstyle="round,pad=0.006",
                                    fc=C_PANEL, ec=C_PANEL_B, lw=0.9))
        ax.text(px + 0.235, PY + PH - 0.010, rotulo, ha="center", va="top",
                fontsize=7.9, fontweight="bold", color=C_TXT2)

    LX, RX, W = 0.036, 0.542, 0.422
    CL, CR = LX + W / 2, RX + W / 2

    # ---- fila 1 -------------------------------------------------------------
    caja(ax, LX, 0.795, W, 0.120, "Line-of-sight engine",
         "profile sampling · curvature + refraction")
    # la linea roja: los defectos viven dentro del motor, conmutables
    ax.text(LX + W / 2, 0.795 + 0.120 - 0.086, "5 switchable defects, injected one at a time",
            ha="center", va="top", fontsize=FS_C, color=C_MAL)
    caja(ax, RX, 0.795, W, 0.120, "Synthetic landscape",
         "anisotropic ridges · lake flooded to a constant")
    for x0 in (CL, CR):
        flecha(ax, x0, 0.792, 0.757)

    # ---- fila 2 -------------------------------------------------------------
    caja(ax, LX, 0.585, W, 0.162, "Benchmark",
         "15 terrain cases, expectations derived\n"
         "(critical distance, not intuition)\n"
         "4 behavioural properties on random terrain")
    caja(ax, RX, 0.585, W, 0.162, "Ground truth by construction",
         "S0 exchangeable → p exactly uniform\n"
         "S1 best of K placements → known power\n"
         "(theoretical ceiling 85 %)")
    for x0 in (CL, CR):
        flecha(ax, x0, 0.582, 0.547)

    # ---- fila 3 -------------------------------------------------------------
    caja(ax, LX, 0.425, W, 0.112, "Mutation analysis",
         "run the whole benchmark against\neach deliberately broken engine")
    caja(ax, RX, 0.425, W, 0.112, "Paired contrasts",
         "correct · water unmasked · tight crop\nsame data; only the defect differs")
    for x0 in (CL, CR):
        flecha(ax, x0, 0.422, 0.385)

    # ---- fila 4: veredictos -------------------------------------------------
    caja(ax, LX, 0.238, W, 0.137, "4 defects killed · 1 equivalent",
         "equivalence proven by paired sweep,\nnot assumed",
         fc=C_OK_F, ec=C_OK, tc="#24512e", tb="#3a5c42")
    caja(ax, RX, 0.238, W, 0.137, "Calibration · power · mechanism",
         "what each defect does to inference,\nmeasured against an exact expectation",
         fc=C_OK_F, ec=C_OK, tc="#24512e", tb="#3a5c42")
    for x0 in (CL, CR):
        flecha(ax, x0, 0.235, 0.188)

    # ---- diagnosticos y desembocadura --------------------------------------
    caja(ax, 0.120, 0.096, 0.760, 0.098, "Diagnostics for any real study",
         "D1: null placements touching water = 0"
         "        D2: orientation coverage = 100 %",
         fc=C_DIAG, ec=C_DIAG_B, tc="#2c4a66", tb="#3a5a78")
    flecha(ax, 0.5, 0.093, 0.078)

    caja(ax, 0.110, 0.014, 0.780, 0.060,
         "Only a validated engine and a diagnosed design touch real terrain",
         fc=C_FIN_F, ec=C_FIN_B, tc="#5c4718", fs_t=8.0)

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
