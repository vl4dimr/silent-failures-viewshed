# -*- coding: utf-8 -*-
"""
Ejecuta el banco sobre el motor correcto y sobre cada version averiada.

Esto es analisis de mutantes, la tecnica estandar para evaluar un conjunto de
pruebas: se introduce a proposito un defecto conocido y se mide si las pruebas
lo detectan. Un banco que aprueba tanto el motor correcto como el averiado no
prueba nada, por muchos casos que tenga.

La lectura es doble. Hacia el motor: si el correcto no pasa todo, hay un error.
Hacia el banco: si un defecto pasa desapercibido, falta una prueba, y eso senala
exactamente que prueba falta.

El banco tambien se audita a si mismo por otros dos lados:

  - cada caso se ejecuta con el rasgo que dice probar retirado; si el veredicto
    no cambia, el caso aprobaba por la razon equivocada (comprobar_rasgo);
  - las cuatro propiedades de la primera version se ejecutan contra los
    mutantes y su resultado —ninguna detecta ninguno— se guarda como hallazgo.

Salida: results/benchmark.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from los_engine import DEFECTOS, R_EFF, line_of_sight
from suite import (RES as CELDA, casos, casos_detallados, comprobar_rasgo,
                   descripcion_geometrica, distancia_critica,
                   distancia_critica_aprox, plano, propiedades, propiedades_v1)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")


def evaluar_casos(defecto):
    det, detectado = [], 0
    for nombre, fn, esperado in casos():
        try:
            obtenido = fn(defecto)
            ok = (obtenido == esperado)
        except Exception as e:
            obtenido, ok = "excepcion: %s" % str(e)[:40], False
        det.append({"prueba": nombre, "esperado": esperado,
                    "obtenido": obtenido, "pasa": ok})
        detectado += (not ok)
    return det, detectado


def evaluar_propiedades(defecto, conjunto):
    det, detectado = [], 0
    for nombre, fn in conjunto():
        try:
            viol, n = fn(defecto)
            ok = (viol == 0)
        except Exception as e:
            viol, n, ok = -1, 0, False
            nombre += " (excepcion: %s)" % str(e)[:30]
        det.append({"prueba": nombre, "violaciones": viol,
                    "comprobaciones": n, "pasa": ok})
        detectado += (not ok)
    return det, detectado


def evaluar(defecto):
    """Devuelve (detalle_casos, detalle_propiedades, n_detecciones)."""
    cs, n1 = evaluar_casos(defecto)
    ps, n2 = evaluar_propiedades(defecto, propiedades)
    return cs, ps, n1 + n2


def es_equivalente(defecto, n_terrenos=250):
    """(equivalente, n_comparaciones): ¿difiere el mutante en algo observable?

    Un mutante que nunca difiere es un mutante equivalente: la mutacion no altera
    el comportamiento observable, y no detectarlo no es un fallo del banco sino
    una propiedad del mutante. Es el confundido clasico del analisis de mutantes,
    y confundirlo con un hueco hace parecer peor un banco que esta bien.
    """
    import numpy as np
    from suite import RES as _RES, rugoso
    rng = np.random.default_rng(7)
    n_comp = 0
    for s_ in range(n_terrenos):
        dem = rugoso(300, semilla=s_)
        for _ in range(6):
            c0, c1 = sorted(int(x) for x in rng.integers(0, 300, 2))
            if c1 - c0 < 3:
                continue
            for ho, ht in ((1.7, 3.0), (0.0, 0.0), (0.0, 3.0), (1.7, 0.0)):
                n_comp += 1
                a = line_of_sight(dem, _RES, _RES, c0, 1, c1, 1, h_obs=ho, h_tgt=ht)
                b = line_of_sight(dem, _RES, _RES, c0, 1, c1, 1, h_obs=ho, h_tgt=ht,
                                  defecto=defecto)
                if a != b:
                    return False, n_comp
    # y con relieve justo en los extremos, donde mas facil seria notarlo
    from suite import con_cima_en
    for col in (0, 299):
        for alt in (5.0, 40.0, 200.0):
            dem = con_cima_en(300, col, altura=alt)
            for ho, ht in ((1.7, 3.0), (0.0, 0.0)):
                n_comp += 1
                a = line_of_sight(dem, _RES, _RES, 0, 1, 299, 1, h_obs=ho, h_tgt=ht)
                b = line_of_sight(dem, _RES, _RES, 0, 1, 299, 1, h_obs=ho, h_tgt=ht,
                                  defecto=defecto)
                if a != b:
                    return False, n_comp
    return True, n_comp


DEMOSTRACION_EXTREMOS = (
    "El termino de curvatura d(D-d)/2R se anula en d = 0 y en d = D, de modo que en "
    "los extremos z_corr[0] = z[0] y z_corr[-1] = z[-1], mientras que la linea vale "
    "z[0] + h_obs y z[-1] + h_tgt. Con h_obs >= 0 y h_tgt >= 0 la condicion de bloqueo "
    "nunca se cumple en los extremos: incluirlos no anade ningun bloqueo. El barrido "
    "solo lo confirma empiricamente; la equivalencia es un teorema para alturas no "
    "negativas, y deja de serlo con alturas negativas (vease el contraejemplo).")


def contraejemplo_alturas_negativas(defecto="extremos_incluidos"):
    """Con h_obs < 0 el mutante deja de ser equivalente. Observador al borde de
    un escarpe de 100 m sobre un valle llano, 1 m por debajo de su suelo: el
    correcto ve el valle a 1 km y el mutante se tapa con su propia celda.
    Acota el dominio del teorema a alturas no negativas."""
    dem = plano(40) - 100.0
    dem[:, 0] += 100.0
    a = bool(line_of_sight(dem, CELDA, CELDA, 0, 1, 33, 1, h_obs=-1.0, h_tgt=3.0))
    b = bool(line_of_sight(dem, CELDA, CELDA, 0, 1, 33, 1, h_obs=-1.0, h_tgt=3.0,
                           defecto=defecto))
    return {"terreno": "escarpe de 100 m bajo el observador, valle llano",
            "h_obs": -1.0, "h_tgt": 3.0, "distancia_km": 33 * CELDA / 1000.0,
            "correcto": a, "mutante": b, "difieren": a != b}


def main():
    os.makedirs(RES, exist_ok=True)
    salida = {"motor_correcto": None, "propiedades_v1": None, "mutantes": {},
              "resumen": None}

    print("BANCO DE PRUEBAS SOBRE EL MOTOR CORRECTO")
    print("=" * 72)
    detallados = casos_detallados()
    cs, ps, fallos = evaluar(None)
    for c, d in zip(cs, detallados):
        c.update(descripcion_geometrica(d))
        c.update(comprobar_rasgo(d))
        marca = "OK" if c["pasa"] else "FALLA"
        rasgo = ("decide" if c["rasgo_decide"] else "no decide")
        aviso = "" if c["comprobacion_rasgo_ok"] else "   <-- RASGO MAL: prueba otra cosa"
        print("  %-5s %-64s %5.1f km  %-7s %s%s"
              % (marca, c["prueba"][:64], c["distancia_km"], c["tipo"], rasgo, aviso))
    print()
    for p in ps:
        print("  %-5s %-52s %d violaciones de %d"
              % ("OK" if p["pasa"] else "FALLA", p["prueba"], p["violaciones"],
                 p["comprobaciones"]))
    total = len(cs) + len(ps)
    print()
    print("  %d de %d pruebas superadas" % (total - fallos, total))

    de_rasgo = [c for c in cs if c["tipo"] == "rasgo"]
    controles = [c for c in cs if c["tipo"] == "control"]
    rasgo_mal = [c["prueba"] for c in cs if not c["comprobacion_rasgo_ok"]]
    comprobacion = {
        "regla": ("cada caso se vuelve a ejecutar con su rasgo retirado (barrera u hondura a "
                  "0 m, objetivo a 0 m, o termino de curvatura apagado). En un caso de tipo "
                  "'rasgo' el veredicto debe cambiar; en un 'control' no debe cambiar. Un caso "
                  "de rasgo cuyo veredicto no cambia aprueba por la razon equivocada."),
        "casos_de_rasgo": len(de_rasgo),
        "casos_de_rasgo_en_que_decide": sum(1 for c in de_rasgo if c["rasgo_decide"]),
        "controles": len(controles),
        "controles_consistentes": sum(1 for c in controles if c["comprobacion_rasgo_ok"]),
        "casos_que_fallan_la_comprobacion": rasgo_mal,
        "ok": not rasgo_mal,
    }
    print("  Comprobacion 'el rasgo decide': %d/%d casos de rasgo deciden, %d/%d controles "
          "consistentes%s"
          % (comprobacion["casos_de_rasgo_en_que_decide"], len(de_rasgo),
             comprobacion["controles_consistentes"], len(controles),
             "" if comprobacion["ok"] else "  <-- FALLA: %s" % rasgo_mal))

    salida["motor_correcto"] = {
        "casos": cs, "propiedades": ps, "pruebas": total, "fallos": fallos,
        "comprobacion_rasgo_decide": comprobacion,
        "celda_m": CELDA,
        "distancia_critica": {
            "h_obs": 1.7, "h_tgt": 3.0, "r_eff_m": R_EFF,
            "exacta_m": distancia_critica(1.7, 3.0),
            "formula": "sqrt(2 R_eff h_obs) + sqrt(2 R_eff h_tgt): suma de las dos "
                       "distancias al horizonte; la recta entre los extremos es tangente "
                       "al abultamiento d(D-d)/2R_eff",
            "aproximada_v1_m": distancia_critica_aprox(1.7, 3.0),
            "formula_v1": "sqrt(8 R_eff (h_obs + h_tgt) / 2): abultamiento en el punto "
                          "medio igual a la altura media de la linea; solo exacta con "
                          "h_obs == h_tgt, sobrestima en el resto",
            "nota": "la version anterior del banco y del manuscrito usaba la formula v1 "
                    "(11.73 km); el motor pierde la vista sobre un plano a 11.62 km, lo que "
                    "la exacta predice. Los casos a 8.7 y 18.6 km se derivan de la exacta.",
        },
    }

    if fallos or not comprobacion["ok"]:
        print("\n  El banco no esta en condiciones: o el motor de referencia falla, o algun caso")
        print("  prueba otra cosa que lo que dice. Nada mas que hacer hasta arreglarlo.")
        json.dump(salida, open(os.path.join(RES, "benchmark.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        return 1

    # -- hallazgo: las propiedades de la primera version contra los mutantes
    print()
    print("PROPIEDADES DE LA PRIMERA VERSION CONTRA LOS MUTANTES (hallazgo)")
    print("=" * 72)
    v1_nombres = [n for n, _ in propiedades_v1()]
    v1_detalle, v1_matan = {}, {}
    for d in DEFECTOS:
        ps1, n_det = evaluar_propiedades(d, propiedades_v1)
        v1_detalle[d] = {p["prueba"]: {"violaciones": p["violaciones"],
                                       "comprobaciones": p["comprobaciones"]} for p in ps1}
        v1_matan[d] = [p["prueba"] for p in ps1 if not p["pasa"]]
        print("  %-24s propiedades v1 que saltan: %d de %d" % (d, len(v1_matan[d]), len(ps1)))
    salida["propiedades_v1"] = {
        "nombres": v1_nombres,
        "mutantes_detectados": sum(1 for d in DEFECTOS if v1_matan[d]),
        "mutantes_evaluados": len(DEFECTOS),
        "cuales_por_mutante": v1_matan,
        "detalle": v1_detalle,
        "por_que": ("las cuatro son condiciones necesarias —simetria en d <-> D-d y "
                    "monotonia en las alturas y en la distancia— que cualquier motor con esa "
                    "estructura cumple, averiado o no: los cinco mutantes las satisfacen. "
                    "Son un ejemplo de la tesis del articulo aplicada a si mismo: pruebas "
                    "que aprueban y no miden nada."),
    }

    print()
    print("ANALISIS DE MUTANTES: ¿detecta el banco cada defecto?")
    print("=" * 72)
    print("  %-24s %8s %7s %7s %7s   %s"
          % ("defecto", "detect.", "casos", "props", "total", "primera que salta"))
    print("  " + "-" * 76)
    for d in DEFECTOS:
        cs_d, ps_d, n_det = evaluar(d)
        fallan_c = [x["prueba"] for x in cs_d if not x["pasa"]]
        fallan_p = [x["prueba"] for x in ps_d if not x["pasa"]]
        fallan = fallan_c + fallan_p
        equiv, n_comp = es_equivalente(d) if n_det == 0 else (False, 0)
        estado = "SI" if n_det else ("equival." if equiv else "NO")
        salida["mutantes"][d] = {
            "detectado": bool(n_det), "equivalente": equiv,
            "comparaciones_equivalencia": n_comp,
            "pruebas_que_saltan": n_det, "de": total, "cuales": fallan,
            "casos_que_saltan": len(fallan_c), "de_casos": len(cs_d), "cuales_casos": fallan_c,
            "propiedades_que_saltan": len(fallan_p), "de_propiedades": len(ps_d),
            "cuales_propiedades": fallan_p,
            "muere_por_caso_y_propiedad": bool(fallan_c) and bool(fallan_p),
            "detalle_propiedades": {x["prueba"]: {"violaciones": x["violaciones"],
                                                  "comprobaciones": x["comprobaciones"]}
                                    for x in ps_d},
        }
        if d == "extremos_incluidos":
            salida["mutantes"][d]["demostracion_equivalencia"] = DEMOSTRACION_EXTREMOS
            salida["mutantes"][d]["contraejemplo_alturas_negativas"] = \
                contraejemplo_alturas_negativas(d)
        print("  %-24s %8s %3d/%-3d %3d/%-3d %3d/%-3d   %s"
              % (d, estado, len(fallan_c), len(cs_d), len(fallan_p), len(ps_d), n_det, total,
                 (fallan[0][:30] if fallan else ("no altera ninguna respuesta" if equiv else "—"))))

    huecos = [d for d, v in salida["mutantes"].items()
              if not v["detectado"] and not v["equivalente"]]
    equivalentes = [d for d, v in salida["mutantes"].items() if v["equivalente"]]
    no_equiv = [d for d in DEFECTOS if d not in equivalentes]
    salida["resumen"] = {
        "casos": len(cs), "propiedades": len(ps), "pruebas": total,
        "casos_de_rasgo": len(de_rasgo), "controles": len(controles),
        "mutantes": len(DEFECTOS), "equivalentes": equivalentes,
        "no_equivalentes": no_equiv,
        "muertos_por_algun_caso": [d for d in no_equiv if salida["mutantes"][d]["casos_que_saltan"]],
        "muertos_por_alguna_propiedad": [d for d in no_equiv
                                         if salida["mutantes"][d]["propiedades_que_saltan"]],
        "muertos_por_caso_y_propiedad": [d for d in no_equiv
                                         if salida["mutantes"][d]["muere_por_caso_y_propiedad"]],
        "huecos": huecos,
        "propiedades_v1_mutantes_detectados": salida["propiedades_v1"]["mutantes_detectados"],
        "todo_mutante_no_equivalente_muere_por_caso_y_propiedad":
            all(salida["mutantes"][d]["muere_por_caso_y_propiedad"] for d in no_equiv),
    }
    print()
    if huecos:
        print("  HUECO EN EL BANCO: no detecta %s" % huecos)
    else:
        print("  El banco detecta todos los defectos con efecto observable.")
    if equivalentes:
        print("  Mutantes equivalentes (la mutacion no cambia ninguna respuesta): %s"
              % equivalentes)
        print("  No son un hueco: son diferencias de implementacion sin consecuencia.")
    print("  Todo mutante no equivalente muere por un caso Y por una propiedad: %s"
          % salida["resumen"]["todo_mutante_no_equivalente_muere_por_caso_y_propiedad"])

    json.dump(salida, open(os.path.join(RES, "benchmark.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\n  ->", os.path.join(RES, "benchmark.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
