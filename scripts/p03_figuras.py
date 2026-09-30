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

Criterios de Springer que se aplican aqui y como se cumplen:
  - los lienzos miden 155 mm de ancho, lo mismo que en el manuscrito, asi que
    los cuerpos nominales son los impresos: nada baja de 8 pt;
  - contraste del rotulado >= 4.5:1 sobre su fondo;
  - la informacion nunca depende solo del color: estilos de linea, marcadores
    distintos y tramas la duplican, porque en papel se imprime en blanco y
    negro y hay lectores con deficiencia rojo-verde;
  - letras de panel en minuscula, (a), (b), ...

Salida: results/figuras/fig_anatomia, fig_laboratorio, fig_consecuencias en
PNG a 300 ppp (el que incrusta el manuscrito), mas PDF vectorial y TIFF (LZW)
por si produccion los pide. meta.json guarda los numeros que el texto cita.
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from los_engine import line_of_sight
from suite import RES as RES1D, con_barrera, rugoso
from terrain_lab import (MARGEN_BORDE, _gauss_suave, _gira, colocacion_S0,
                        forma_alargada, intento_colocacion, paisaje,
                        region_ajustada, cobertura_orientaciones)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
FIG = os.path.join(RES, "figuras")

# El sistema visual de la figura 1 (pipeline), aplicado a los graficos de datos:
# tinta y grises para la estructura, azul para lo corregido/el agua como
# procedimiento, rojo como unico acento semantico (defectos, bloqueos, exclusiones).
# Cuerpos: 9 pt titulos de panel, 8.5 pt rotulos de eje, 8 pt todo lo demas.
FS_TIT, FS_LAB, FS_TXT = 9.0, 8.5, 8.0
plt.rcParams.update({
    "font.family": "Arial", "font.size": FS_TXT,
    "axes.titlesize": FS_TIT, "axes.labelsize": FS_LAB,
    "xtick.labelsize": FS_TXT, "ytick.labelsize": FS_TXT,
    "legend.fontsize": FS_TXT,
    "axes.linewidth": 0.6, "axes.edgecolor": "#c7cdd6",
    "xtick.color": "#4b5563", "ytick.color": "#4b5563",
    "axes.labelcolor": "#374151", "text.color": "#111827",
    "hatch.linewidth": 0.5,
    "pdf.fonttype": 42,          # TrueType incrustada, no Type 3: lo que pide produccion
})

C_TERRENO = "#a8a29e"
C_TERRENO_L = "#e7e5e4"
C_CORR = "#2b5da8"
C_VISTA = "#111827"
C_MAL = "#b91c1c"
C_OK = "#475569"
C_AGUA = "#c9d8e8"
C_NULO = "#374151"


def guardar(fig, nombre, **kw):
    """PNG a 300 ppp para el manuscrito; PDF vectorial y TIFF LZW para produccion.

    El TIFF sale del mismo PNG, aplanado sobre blanco y en RGB sin canal alfa,
    que es lo que un flujo de imprenta espera.
    """
    from PIL import Image
    png = os.path.join(FIG, nombre + ".png")
    fig.savefig(png, dpi=300, **kw)
    fig.savefig(os.path.join(FIG, nombre + ".pdf"), **kw)
    im = Image.open(png)
    plano = Image.new("RGB", im.size, (255, 255, 255))
    plano.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
    plano.save(os.path.join(FIG, nombre + ".tif"), compression="tiff_lzw",
               dpi=(300, 300))


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


def veredicto(ax, texto, color):
    """El veredicto del motor, abajo a la derecha, sobre el relleno del terreno."""
    ax.text(0.985, 0.06, texto, transform=ax.transAxes, ha="right",
            fontsize=FS_TIT, fontweight="bold", color=color)


def perfil(ax, dem, c1, defecto, titulo, texto_v, color_v):
    _, pr = line_of_sight(dem, RES1D, RES1D, 0, 1, c1, 1, defecto=defecto,
                          return_profile=True)
    km = pr["d"] / 1000.0
    z0 = pr["z"].min() - 15
    # tres trazos distinguibles sin color: el terreno es el borde del relleno,
    # el corregido una linea continua mas gruesa, la visual una discontinua
    ax.fill_between(km, z0, pr["z"], color=C_TERRENO_L, lw=0)
    ax.plot(km, pr["z"], color=C_TERRENO, lw=0.7, label="terrain")
    ax.plot(km, pr["z_corr"], color=C_CORR, lw=1.2,
            label="terrain, curvature-corrected")
    ax.plot(km, pr["vista"], color=C_VISTA, lw=1.0, ls="--", label="line of sight")
    # la franja donde el terreno corregido supera la visual
    exceso = pr["z_corr"] > pr["vista"]
    exceso[0] = exceso[-1] = False
    if exceso.any():
        ax.fill_between(km, pr["vista"], pr["z_corr"], where=exceso,
                        color=C_MAL, alpha=0.55, lw=0)
        # cuanto sobresale el relieve que decide: la sutileza es el argumento
        i = int(np.argmax(np.where(exceso, pr["z_corr"] - pr["vista"], -1)))
        ax.annotate("obstruction: %.1f m above the line" % (pr["z_corr"][i] - pr["vista"][i]),
                    xy=(km[i], pr["z_corr"][i]), xytext=(0.04, 0.91),
                    textcoords="axes fraction", ha="left", va="top",
                    fontsize=FS_TXT, color=C_MAL,
                    arrowprops=dict(arrowstyle="-", color=C_MAL, lw=0.7,
                                    shrinkA=1, shrinkB=2))
    ax.set_title(titulo, loc="left")
    veredicto(ax, texto_v, color_v)
    ax.set_ylim(z0, pr["z"].max() + 40)
    ax.margins(x=0)


def figura1():
    dem, c1, sem = buscar_par_curvatura()
    fig, axs = plt.subplots(2, 2, figsize=(6.10, 5.25))

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
    z0 = prb["z"].min() - 22          # sitio para el veredicto bajo el terreno
    ax.fill_between(kmb, z0, prb["z"], color=C_TERRENO_L, lw=0)
    ax.plot(kmb, prb["z"], color=C_TERRENO, lw=0.7)
    ax.plot(prg["d"] / 1000.0, prg["z"], "o", ms=4.6, color=C_MAL, mfc="white",
            mew=0.9, label="coarse samples (10)")
    ax.plot(kmb, prb["vista"], color=C_VISTA, lw=1.0, ls="--")
    ax.set_title("(c) Coarse sampling misses an 80 m barrier", loc="left")
    veredicto(ax, "CLEAR", C_OK)
    ax.set_ylim(z0, prb["z"].max() + 10)
    ax.margins(x=0)

    # (d) el mismo par de (a) recortado a corta distancia: todo motor coincide
    c_corto = int(c1 * 0.15)
    perfil(axs[1, 1], dem, c_corto, None,
           "(d) At %.1f km every variant agrees" % (c_corto * RES1D / 1000),
           "CLEAR", C_OK)

    for ax in axs.flat:
        ax.set_xlabel("distance (km)")
        ax.set_ylabel("elevation (m)")
    # una sola leyenda para los cuatro paneles, bajo la figura
    h_a, l_a = axs[0, 0].get_legend_handles_labels()
    h_c, l_c = axs[1, 0].get_legend_handles_labels()
    fig.legend(h_a + h_c, l_a + l_c, loc="lower center", ncol=4, frameon=False,
               handlelength=2.4, columnspacing=1.6, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(pad=1.1, rect=(0, 0.05, 1, 1))
    guardar(fig, "fig_anatomia")
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


def barras_orientacion(ax, caben, titulo):
    """Que orientaciones caben (barra llena) y cuales no (trama), por tramos.

    Una barra por tramo contiguo, para que la trama sea continua; el rotulo
    va sobre el tramo mas ancho de cada clase, asi que se lee sin leyenda y
    sin color.
    """
    caben = np.asarray(caben, dtype=int)
    tramos = []
    i = 0
    while i < len(caben):
        j = i
        while j < len(caben) and caben[j] == caben[i]:
            j += 1
        tramos.append((i, j, bool(caben[i])))
        i = j
    for i, j, cabe in tramos:
        if cabe:
            ax.add_patch(Rectangle((i, 0), j - i, 1, facecolor=C_OK, edgecolor="none"))
        else:
            ax.add_patch(Rectangle((i, 0), j - i, 1, facecolor="#ffffff",
                                   edgecolor="#9ca3af", hatch="////", lw=0))
    for clase, texto, color, caja in ((True, "fits", "#ffffff", None),
                                      (False, "excluded", "#111827",
                                       dict(facecolor="#ffffff", edgecolor="none", pad=1.6))):
        candidatos = [(j - i, i, j) for i, j, cabe in tramos if cabe == clase]
        if not candidatos:
            continue
        ancho, i, j = max(candidatos)
        if ancho == len(caben):
            texto = "all 360 orientations fit"
        ax.text((i + j) / 2.0, 0.5, texto, ha="center", va="center",
                fontsize=FS_TXT, color=color, bbox=caja)
    ax.set_xlim(0, len(caben))
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_xlabel("orientation of the null placement (°)")
    ax.set_title(titulo, loc="left")


def figura2():
    dem, agua, theta = paisaje(semilla=7)
    rng = np.random.default_rng(41)
    dc, dr = forma_alargada(rng)
    cc, fr, ang = colocacion_S0(dem, agua, dc, dr, rng)
    reg = region_ajustada(cc, fr, dem, 25)
    cob_full = cobertura_orientaciones(dem, dc, dr)
    cob_tight = cobertura_orientaciones(dem, dc, dr, reg)

    # Geometria calculada para que el mapa (cuadrado) llene exactamente su
    # celda y nada sobresalga de los 155 mm: asi el PNG mide lo que el lienzo.
    fig = plt.figure(figsize=(6.10, 4.05))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.36, 1], hspace=0.62, wspace=0.10,
                          left=0.02, right=0.975, top=0.93, bottom=0.14)

    # (a) el paisaje
    ax = fig.add_subplot(gs[:, 0])
    sh = sombreado(dem)
    ax.imshow(sh, cmap="gray", vmin=0, vmax=1, alpha=0.9)
    ax.imshow(np.ma.masked_where(~agua, np.ones_like(dem)), cmap=
              matplotlib.colors.ListedColormap([C_AGUA]), alpha=0.95)
    # la orilla, dibujada: en gris el lago se distingue por su contorno y su
    # tono plano, no solo por el azul
    ax.contour(agua.astype(float), levels=[0.5], colors="#6b7280", linewidths=0.5)
    interior = _gauss_suave(agua.astype(float), 9.0)
    interior[~agua] = -1.0
    f_lago, c_lago = np.unravel_index(int(np.argmax(interior)), interior.shape)
    ax.text(c_lago, f_lago, "lake", ha="center", va="center", fontsize=FS_TXT,
            style="italic", color="#374151")
    # colocaciones nulas fantasma: anillos huecos frente a los puntos llenos
    # de la nube observada, para que se separen tambien en blanco y negro
    rng2 = np.random.default_rng(5)
    fantasmas = 0
    while fantasmas < 3:
        col = intento_colocacion(dem, agua, dc, dr, rng2)
        if col is None:
            continue
        ax.plot(col[0], col[1], "o", ms=2.9, mfc="none", mec=C_NULO, mew=0.6)
        fantasmas += 1
    ax.plot(cc, fr, "o", ms=3.8, color=C_MAL, mec="#ffffff", mew=0.4)
    rmin, rmax, cmin, cmax = reg
    ax.add_patch(Rectangle((cmin, rmin), cmax - cmin, rmax - rmin,
                           fill=False, ec=C_MAL, lw=1.1, ls="--"))
    ax.set_title("(a) One synthetic replicate", loc="left")
    ax.set_xticks([]); ax.set_yticks([])
    # barra de escala: 5 km son 167 celdas de 30 m
    h, w = dem.shape
    x0, y0, celdas = w * 0.05, h * 0.95, 5000.0 / 30.0
    ax.plot([x0, x0 + celdas], [y0, y0], color="#111827", lw=2.2,
            solid_capstyle="butt")
    ax.text(x0 + celdas / 2, y0 - 7, "5 km", ha="center", fontsize=FS_TXT,
            bbox=dict(facecolor="#ffffff", edgecolor="none", pad=1.4, alpha=0.9))
    manijas = [
        Line2D([], [], ls="", marker="o", ms=3.8, color=C_MAL, mec="#ffffff",
               mew=0.4, label="observed cloud (32 sites)"),
        Line2D([], [], ls="", marker="o", ms=2.9, mfc="none", mec=C_NULO,
               mew=0.6, label="null placements (three shown)"),
        Line2D([], [], ls="--", lw=1.1, color=C_MAL,
               label="tightly cropped sampling region"),
    ]
    # una fila a pie de figura, bajo las dos columnas
    fig.legend(handles=manijas, loc="lower center", bbox_to_anchor=(0.5, 0.0),
               ncol=3, frameon=False, borderaxespad=0, handletextpad=0.5,
               columnspacing=1.4, handlelength=2.0)

    # (b) y (c): cobertura de orientaciones, region completa y recortada
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
        barras_orientacion(ax, caben, tit)
    guardar(fig, "fig_laboratorio")
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
    # clave, rotulo, color, estilo de linea, marcador: cada procedimiento se
    # distingue por la forma ademas de por el color
    PROCS = [("correcto", "correct", C_OK, "-", "o"),
             ("agua", "water unmasked", C_CORR, "--", "^"),
             ("recorte", "tight crop", C_MAL, "-.", "D")]

    fig, axs = plt.subplots(1, 3, figsize=(6.10, 2.95))

    # (a) calibracion: ECDF de p en S0
    ax = axs[0]
    ax.plot([0, 1], [0, 1], color="#999999", lw=0.8, ls=":", zorder=1)
    for clave, eti, color, ls, _ in PROCS:
        ps = np.sort([r["S0"][clave]["p"] for r in reps])
        ax.step(np.concatenate([[0], ps]),
                np.concatenate([[0], np.arange(1, len(ps) + 1) / len(ps)]),
                where="post", color=color, lw=1.3, ls=ls, label=eti)
    ax.set_xlabel("p value under no effect (S0)")
    ax.set_ylabel("empirical CDF")
    ax.set_title("(a) Calibration under S0", loc="left")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    # (b) potencia: z en S1 por procedimiento
    ax = axs[1]
    rng = np.random.default_rng(3)
    etiquetas = []
    for i, (clave, eti, color, _, marca) in enumerate(PROCS):
        zs = np.array([r["S1"][clave]["z"] for r in reps])
        xj = i + rng.uniform(-0.13, 0.13, len(zs))
        ax.plot(xj, zs, marca, ms=3.3, color=color, alpha=0.7, mec="none")
        ax.hlines(np.mean(zs), i - 0.24, i + 0.24, color=color, lw=1.8)
        corta = {"correct": "correct", "water unmasked": "water",
                 "tight crop": "crop"}[eti]
        # la potencia va bajo cada columna, no flotando sobre los puntos
        etiquetas.append("%s\n%.0f %%"
                         % (corta, 100 * res["S1"][clave]["rechazo"]))
    ax.axhline(0, color="#c7cdd6", lw=0.6, ls=":")
    ax.set_xticks(range(len(PROCS)))
    ax.set_xticklabels(etiquetas)
    ax.set_xlim(-0.5, len(PROCS) - 0.5)
    ax.set_ylabel("z under a real effect (S1)")
    ax.set_title("(b) Power under S1, ceiling %.0f %%"
                 % (100 * res["potencia_teorica_S1_correcto"]), loc="left")

    # (c) mecanismo del recorte
    ax = axs[2]
    des = [r["S0"]["desalineacion_grados"] for r in reps]
    dz = [r["S0"]["recorte"]["z"] - r["S0"]["correcto"]["z"] for r in reps]
    ax.axhline(0, color="#999999", lw=0.6, ls=":")
    ax.plot(des, dz, "D", ms=3.3, color=C_MAL, alpha=0.75, mec="none")
    m = res["mecanismo_recorte"]
    ax.set_xlabel("cloud–grain misalignment (°)")
    ax.set_ylabel(r"$\Delta z$ (tight crop $-$ correct)")
    ax.set_xlim(-2, 92)
    ax.set_xticks([0, 30, 60, 90])
    # hueco limpio sobre los puntos para la correlacion
    ax.set_ylim(min(dz) - 0.3, max(dz) + 1.0)
    p_rho = ("p < 0.001" if m["p_spearman"] < 0.001
             else "p = %.3f" % m["p_spearman"])
    ax.set_title("(c) Crop bias mechanism", loc="left")
    rho = ("%.2f" % m["spearman_desalineacion"]).replace("-", "−")
    ax.text(0.04, 0.95, r"$\rho_s$ = %s, %s" % (rho, p_rho),
            transform=ax.transAxes, ha="left", va="top", fontsize=FS_TXT,
            color="#374151")

    # una leyenda para toda la figura: linea (a) y marcador (b, c) de cada
    # procedimiento, fuera de los paneles para no pisar ninguna curva
    manijas = [Line2D([], [], color=color, ls=ls, lw=1.3, marker=marca, ms=3.6,
                      mec="none", label=eti)
               for _, eti, color, ls, marca in PROCS]
    fig.legend(handles=manijas, loc="lower center", ncol=3, frameon=False,
               handlelength=3.0, columnspacing=2.0, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(pad=1.1, w_pad=1.6, rect=(0, 0.085, 1, 1))
    guardar(fig, "fig_consecuencias")
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
