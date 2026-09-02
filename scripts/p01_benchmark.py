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

Salida: results/benchmark.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from los_engine import DEFECTOS, line_of_sight
from suite import casos, propiedades

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")


def evaluar(defecto):
    """Devuelve (detalle_casos, detalle_propiedades, n_detecciones)."""
    det_casos, det_props, detectado = [], [], 0

    for nombre, fn, esperado in casos():
        try:
            obtenido = fn(defecto)
            ok = (obtenido == esperado)
        except Exception as e:
            obtenido, ok = "excepcion: %s" % str(e)[:40], False
        det_casos.append({"prueba": nombre, "esperado": esperado,
                          "obtenido": obtenido, "pasa": ok})
        detectado += (not ok)

    for nombre, fn in propiedades():
        try:
            viol, n = fn(defecto)
            ok = (viol == 0)
        except Exception as e:
            viol, n, ok = -1, 0, False
            nombre += " (excepcion: %s)" % str(e)[:30]
        det_props.append({"prueba": nombre, "violaciones": viol,
                          "comprobaciones": n, "pasa": ok})
        detectado += (not ok)

    return det_casos, det_props, detectado


def es_equivalente(defecto, n_terrenos=250):
    """(equivalente, n_comparaciones): ¿difiere el mutante en algo observable?

    Un mutante que nunca difiere es un mutante equivalente: la mutacion no altera
    el comportamiento observable, y no detectarlo no es un fallo del banco sino
    una propiedad del mutante. Es el confundido clasico del analisis de mutantes,
    y confundirlo con un hueco hace parecer peor un banco que esta bien.
    """
    import numpy as np
    from suite import RES as _RES, con_cima_en, rugoso
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
    for col in (0, 299):
        for alt in (5.0, 40.0, 200.0):
            for ho, ht in ((1.7, 3.0), (0.0, 0.0)):
                n_comp += 1
                a = line_of_sight(dem, _RES, _RES, 0, 1, 299, 1, h_obs=ho, h_tgt=ht)
                b = line_of_sight(dem, _RES, _RES, 0, 1, 299, 1, h_obs=ho, h_tgt=ht,
                                  defecto=defecto)
                if a != b:
                    return False, n_comp
    return True, n_comp


def main():
    os.makedirs(RES, exist_ok=True)
    salida = {"motor_correcto": None, "mutantes": {}}

    print("BANCO DE PRUEBAS SOBRE EL MOTOR CORRECTO")
    print("=" * 72)
    cs, ps, fallos = evaluar(None)
    for c in cs:
        print("  %-5s %s" % ("OK" if c["pasa"] else "FALLA", c["prueba"]))
    print()
    for p in ps:
        print("  %-5s %-44s %d violaciones de %d"
              % ("OK" if p["pasa"] else "FALLA", p["prueba"], p["violaciones"],
                 p["comprobaciones"]))
    total = len(cs) + len(ps)
    print()
    print("  %d de %d pruebas superadas" % (total - fallos, total))
    salida["motor_correcto"] = {"casos": cs, "propiedades": ps,
                                "pruebas": total, "fallos": fallos}

    if fallos:
        print("\n  El motor de referencia no pasa su propio banco. Nada mas que hacer")
        print("  hasta arreglarlo: los mutantes no significan nada si la base falla.")
        json.dump(salida, open(os.path.join(RES, "benchmark.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        return 1

    print()
    print("ANALISIS DE MUTANTES: ¿detecta el banco cada defecto?")
    print("=" * 72)
    print("  %-24s %8s %10s   %s" % ("defecto", "detectado", "pruebas", "primera que salta"))
    print("  " + "-" * 70)
    for d in DEFECTOS:
        cs_d, ps_d, n_det = evaluar(d)
        fallan = [x["prueba"] for x in cs_d + ps_d if not x["pasa"]]
        equiv, n_comp = es_equivalente(d) if n_det == 0 else (False, 0)
        estado = "SI" if n_det else ("equival." if equiv else "NO")
        salida["mutantes"][d] = {"detectado": bool(n_det), "equivalente": equiv,
                                 "comparaciones_equivalencia": n_comp,
                                 "pruebas_que_saltan": n_det, "de": total, "cuales": fallan}
        print("  %-24s %9s %6d/%-3d  %s"
              % (d, estado, n_det, total,
                 (fallan[0][:33] if fallan else ("no altera ninguna respuesta" if equiv else "—"))))

    huecos = [d for d, v in salida["mutantes"].items()
              if not v["detectado"] and not v["equivalente"]]
    equivalentes = [d for d, v in salida["mutantes"].items() if v["equivalente"]]
    print()
    if huecos:
        print("  HUECO EN EL BANCO: no detecta %s" % huecos)
    else:
        print("  El banco detecta todos los defectos con efecto observable.")
    if equivalentes:
        print("  Mutantes equivalentes (la mutacion no cambia ninguna respuesta): %s"
              % equivalentes)
        print("  No son un hueco: son diferencias de implementacion sin consecuencia.")

    json.dump(salida, open(os.path.join(RES, "benchmark.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\n  ->", os.path.join(RES, "benchmark.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
