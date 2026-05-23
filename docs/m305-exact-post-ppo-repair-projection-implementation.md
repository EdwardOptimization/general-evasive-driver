# M305 Exact Post-PPO Repair Projection Implementation

M305 implements the exact post-PPO repair/projection infrastructure designed in
M304. No PPO was run, no checkpoint was promoted, and actor inputs are
unchanged.

## Implemented Tool

New module:

```text
src/autodrift/exact_post_ppo_repair.py
```

CLI:

```bash
PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt \
  --raw-checkpoint runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --start-mode line_search_boundary
```

The tool supports:

- deterministic full-batch exact M297 rejected-history preference loss;
- deterministic full-batch exact M270 outcome-intervention loss;
- line-search boundary starts from M299 to M302 raw;
- repair starts from M299 base or M302 raw;
- exact M270 snippet action anchors to the M299 base;
- parameter L2 trust-region terms to M299 base and optionally M302 raw;
- candidate summaries before replay gates.

The exact losses are first-class output fields. Sampled training losses are not
used as acceptance evidence.

## Real-Corpus Smoke

M305 ran an evaluation-only smoke with `steps=0`:

```text
runs/m305_exact_post_ppo_repair_projection_smoke
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt \
  --raw-checkpoint runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode line_search_boundary \
  --line-search-alphas 0,0.001,0.0025 \
  --steps 0 \
  --run-dir runs/m305_exact_post_ppo_repair_projection_smoke
```

Result:

| Policy | Exact M297 | Exact M270 | Delta M297 | Delta M270 | Exact pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M299 base | 1.189609528 | 0.677945912 | 0.000000000 | 0.000000000 | true |
| M302 raw | 1.190309286 | 0.678388774 | +0.000699759 | +0.000442863 | false |
| candidate step0 | 1.189609528 | 0.677945912 | 0.000000000 | 0.000000000 | true |

Line-search boundary summary:

| Alpha | Delta M297 | Delta M270 | Exact pass |
| ---: | ---: | ---: | --- |
| 0.0000 | 0.000000000 | 0.000000000 | true |
| 0.0010 | +0.000000715 | +0.000000358 | false |
| 0.0025 | +0.000001788 | +0.000001013 | false |

This reproduces the M303 conclusion in the new tool: M302 raw and nonzero
tested interpolation alphas are not exact-admissible without repair. The
`steps=0` candidate equals the base and is not a promoted driver.

## Tests

Focused tests added:

```text
tests/test_exact_post_ppo_repair.py
```

Covered behavior:

- alpha-list validation;
- deterministic full-batch M297 and M270 losses are seed-independent;
- repair loss hinges are zero at the exact base within tolerance;
- action-anchor and parameter trust-region terms are differentiable.

Validation run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_exact_post_ppo_repair.py
PYTHONPATH=src python -m compileall -q src tests
git diff --check
```

## Interpretation

M305 completes the missing infrastructure layer. The project can now test PPO
as a proposal source under exact repair discipline:

```text
proposal checkpoint -> deterministic exact repair -> exact M297/M270 gate -> replay gates
```

The next milestone should run an actual repair/projection probe against M302
raw. That probe must remain gated by exact M297 and exact M270 before any replay
evaluation.

## Decision

Admit:

```text
m306-repair-m302-raw-exact-projection-probe
```

Decision:

```text
admit_m306_exact_repair_probe
```
