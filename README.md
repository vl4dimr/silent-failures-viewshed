# Reproducible and wrong

Silent failures in archaeological visibility analysis, and the instruments to
catch them. Companion repository for the manuscript of the same title.

## The claim

Computational reproducibility guarantees that an analysis can be re-run and
will return the same numbers. It does not guarantee that the numbers are true:
**a reproducible pipeline reproduces its errors with perfect fidelity**. In
visibility analysis a whole class of defects crashes nothing, produces
plausible and interpretable output, survives peer review and re-execution, and
inverts or erases the conclusion of the study that contains them. Three members
of the class were documented in a field study of the Titicaca basin
(doi:10.5281/zenodo.22176260); this repository reproduces them under controlled
conditions and measures exactly what they do to statistical inference.

## The two instruments

**A benchmark for line-of-sight engines** ([scripts/suite.py](scripts/suite.py)):
terrain cases whose expected answer is *derived* (the critical distance at
which Earth curvature severs the view over a plane follows from
D²/8R = (hₒ+hₜ)/2, not from anybody's intuition), plus behavioural
properties —reciprocity, three monotonicities— checked over hundreds of
random terrains. The benchmark's own adequacy is measured, not asserted:
[scripts/los_engine.py](scripts/los_engine.py) can switch on five named
defects, and [scripts/p01_benchmark.py](scripts/p01_benchmark.py) runs the
mutation analysis. Every defect with observable consequences is detected; one
(including the endpoints in the blocking test) is proven behaviourally
equivalent to the correct engine, which is a finding, not a hole.

**A landscape laboratory with ground truth by construction**
([scripts/terrain_lab.py](scripts/terrain_lab.py)): synthetic anisotropic
terrains with a lake, where the no-effect scenario places the observed sites by
the very rules the null model uses —making the p-value of a correct contrast
*exactly* uniform, by exchangeability— and the with-effect scenario places
them at the best of K random placements, making the tested hypothesis true by
construction with known theoretical power.
[scripts/p02_calibracion.py](scripts/p02_calibracion.py) then injects the two
design-level defects (null placements over water; a tightly cropped sampling
region) and measures calibration, power, and mechanism.

**Two production engines under the same benchmark**
([scripts/p07_motores_reales.py](scripts/p07_motores_reales.py),
[scripts/p08_grass_viewshed.py](scripts/p08_grass_viewshed.py),
[scripts/p09_comparacion_motores.py](scripts/p09_comparacion_motores.py)):
the 15 terrain cases are materialised as small rasters and submitted through
`qgis_process` to `gdal_viewshed` (GDAL, QGIS 3.44.13) and `r.viewshed` (GRASS
8.5.0), each run twice — with this study's parameters and with the values it
ships with. Both pass 15/15 when configured; at their defaults GDAL fails 4
(target height 0: blocks the visible) and GRASS fails 3 (no curvature unless
`-c`: sees the blocked), and they contradict each other on 7 of 15 cases.
`results/comparacion_motores.json`.

## Headline results

- The water defect does not create false positives; it **destroys power**. Its
  polarity is what makes it vicious: no spurious discovery ever gets retracted,
  true effects simply are never seen.
- The crop defect miscalibrates in a direction that **depends on the alignment
  between the site configuration and the terrain grain** — unknowable a
  priori, which is precisely why it is silent.
- Two diagnostics flag both defects without ground truth, at negligible cost:
  the fraction of null placements touching water (must be 0) and the fraction
  of the 360 placement orientations that fit the sampling region (must be 100 %).
- Five hand-written test expectations written *during this research* were wrong,
  all five for the same root cause the benchmark targets. Expectations are code
  and fail like code; derive them, and audit the tests by mutation analysis.

## Running it

Everything depends on NumPy alone (Matplotlib for figures, python-docx for the
manuscript). In order:

```bash
python scripts/p01_benchmark.py     # banco + analisis de mutantes  (~2 min)
python scripts/p02_calibracion.py   # laboratorio de calibracion    (~15 min)
python scripts/p03_figuras.py       # las tres figuras
python scripts/p04_manuscript.py    # manuscrito desde los JSON (version JAMT)
python scripts/p05_auditoria.py     # auditoria del manuscrito contra las normas de Springer
python scripts/p07_motores_reales.py      # gdal_viewshed via qgis_process (requiere QGIS 3.44)
python scripts/p08_grass_viewshed.py      # GRASS r.viewshed via qgis_process, con y sin -c
python scripts/p09_comparacion_motores.py # cruza ambos -> results/comparacion_motores.json
python scripts/p10_envio_jamt.py          # paquete ENVIO_JAMT/: manuscrito, Fig1..Fig4, carta
```

No number in the manuscript is typed by hand: every figure that comes from a
computation is read from `results/*.json`, and the audit verifies it.

## Layout

```
scripts/          los_engine, suite, terrain_lab + pipeline p01..p10
results/          benchmark.json, calibracion.json, comparacion_motores.json,
                  motores_reales.json, grass_viewshed.json, auditoria.json, figuras/
data/caso_titicaca/   the three field-study result files the paper cites
ENVIO_JAS/        the package submitted to JAS on 2 Sept 2026 (desk-rejected next day)
ENVIO_JAMT/       the package for Journal of Archaeological Method and Theory
```

## Status

Submitted to the Journal of Archaeological Science on 2 September 2026 and
returned without review the next day. Re-targeted to the Journal of
Archaeological Method and Theory (Springer, single-blind, no charge via the
subscription route): manuscript rewritten to the journal's guidelines on
26 September 2026 — background section on viewshed uncertainty and scientific
software correctness, production-engine measurement, APA 7 references with DOI
links, `Fig. n` captions, Statements and Declarations, LLM use documented in
Methods — 6 229 words of main text, 36 references, 4 figures, 4 tables, 237-word
abstract. Audit: 60 checks, 0 failures. Before submitting, publish a new Zenodo
version (v1.1.0) with the engine-comparison scripts and results.

## Licence

MIT. The field-study files in `data/caso_titicaca/` come from the deposit
cited above (also MIT).
