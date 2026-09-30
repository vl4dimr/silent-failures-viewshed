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
which Earth curvature severs the view over a plane is the sum of the two
horizon distances, √(2Rhₒ) + √(2Rhₜ), not anybody's intuition; the first
version used the mid-path approximation D²/8R = (hₒ+hₜ)/2, exact only for
equal heights), plus four metamorphic
properties —reciprocity with swapped heights, a dominant obstacle at any
interior cell, the derived critical distance over a plane, monotonicity and
sufficiency of observer and target heights— checked over random terrains with
fixed seeds. Every case is also re-run with the feature it is named after
removed, and must change its verdict (or, for a control, must not). The four
properties of the first version killed no mutant; that result is kept in
`results/benchmark.json` (`propiedades_v1`). The benchmark's own adequacy is measured, not asserted:
[scripts/los_engine.py](scripts/los_engine.py) can switch on five named
defects, and [scripts/p01_benchmark.py](scripts/p01_benchmark.py) runs the
mutation analysis. Every defect with observable consequences is killed by at
least one case and at least one property; one
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
the 15 terrain cases are materialised as small rasters and passed directly to
the command-line programs shipped with QGIS 3.44.13 — `gdal_viewshed` (GDAL
3.13.2) and `r.viewshed` (GRASS 8.5.0), not through `qgis_process` — each run
with this study's parameters and with only its mandatory arguments. Both pass
15/15 when configured. As shipped, GDAL fails 4 (target height 0: blocks the
visible; `-tz` alone accounts for all four) and GRASS fails 5 in both
directions (target height 0 and no curvature unless `-c`); they disagree on 3
cases and share the same error on 3. `results/comparacion_motores.json`.

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
- The benchmark failed silently too: five handwritten expectations forgot the
  curvature term, three feature cases still passed on curvature alone until the
  "feature decides" check moved them, the four first-version properties killed
  no mutant, and the first r.viewshed runs passed `refraction_coeff` without the
  `-r` flag that activates it. Expectations and properties are code and fail
  like code; derive them, check why they pass, and audit them by mutation analysis.
- Agreement between two programs validates nothing: at their shipped defaults
  gdal_viewshed and r.viewshed disagree on 3 of 15 cases and return the *same*
  wrong verdict on 3 others (a target on the ground by default in both).

## Running it

Everything depends on NumPy alone (Matplotlib for figures, python-docx for the
manuscript). In order:

```bash
python scripts/p01_benchmark.py     # banco + analisis de mutantes  (~2 min)
python scripts/p02_calibracion.py   # laboratorio de calibracion    (~15 min)
python scripts/p03_figuras.py       # las tres figuras
python scripts/p04_manuscript.py    # manuscrito desde los JSON (version JAMT)
python scripts/p05_auditoria.py     # auditoria del manuscrito contra las normas de Springer
python scripts/p07_motores_reales.py      # gdal_viewshed.exe directo (requiere QGIS 3.44)
python scripts/p08_grass_viewshed.py      # r.viewshed via grass85.bat --exec, configurado y de fabrica
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
Methods. Final revision on 30 September 2026 after five internal reviews
(computation, science, references, Springer production, English): corrected
benchmark (7 feature cases + 8 controls), exact critical distance, new
properties and the first-version finding, engines invoked directly at their
full shipped defaults, declared statistics, two new tables (the 15 cases; the
parameters every visibility study should declare), italic APA 7 references and
British typography — 8 591 words of main text plus 702 in tables, 49
references, 4 figures (PDF + TIFF in `ENVIO_JAMT/`), 6 tables, 247-word
abstract. Audit: 107 checks, 0 failures. Before submitting, publish a new
Zenodo version (v1.2.0) so that the concept DOI resolves to the code that
produced these numbers.

## Licence

MIT. The field-study files in `data/caso_titicaca/` come from the deposit
cited above (also MIT).
