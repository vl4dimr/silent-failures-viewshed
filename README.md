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
python scripts/p04_manuscript.py    # manuscrito desde los JSON
python scripts/p05_auditoria.py     # auditoria del manuscrito
```

No number in the manuscript is typed by hand: every figure that comes from a
computation is read from `results/*.json`, and the audit verifies it.

## Layout

```
scripts/          los_engine, suite, terrain_lab + pipeline p01..p05
results/          benchmark.json, calibracion.json, auditoria.json, figuras/
data/caso_titicaca/   the three field-study result files the paper cites
```

## Licence

MIT. The field-study files in `data/caso_titicaca/` come from the deposit
cited above (also MIT).
