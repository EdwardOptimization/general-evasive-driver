# M389 M267 Row15 Conflict Corpus Implementation

M389 implements the current-family conflict corpus and optional exact-repair
residual designed in M388. It does not run PPO, promote a checkpoint, lower
thresholds, or change the actor input/output contract.

## Scope

Current public-gate base:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

The active conflict is:

```text
old-key normal-margin recovery
vs
M267/M264 wrong-history failure retention
```

M389 makes that conflict visible to exact repair through a compact corpus with
two current-family rows:

| Row | Physical pair | Boundary wrong-history margin | Weight |
| ---: | --- | ---: | ---: |
| 15 | `9530:21:9550:21` | -0.000001064 | 0.234873593 |
| 6 | `9530:15:9550:18` | -0.000059669 | 0.034303833 |

Row `15` receives the larger weight because it is closest to crossing into
wrong-history success under the M385 recovery direction.

## Implementation

Added:

```text
src/autodrift/current_family_conflict_corpus.py
```

This exporter reads the M267/M264 boundary corpus plus replay margins, computes
preferred and wrong-history base actions from the current checkpoint, and writes:

```text
runs/m389_m267_row15_conflict_corpus/current_family_conflict_corpus.npz
runs/m389_m267_row15_conflict_corpus/current_family_conflict_rows.csv
```

The NPZ schema is:

```text
observation
preferred_hidden
rejected_hidden
preferred_anchor_action
rejected_boundary_action
weight
row_id
boundary_margin
```

Added loader validation in:

```text
src/autodrift/intervention_objectives.py
```

The loader checks non-empty rows, observation/hidden/action shapes, finite
values, action bounds, and at least one positive weight.

Added optional exact-repair terms in:

```text
src/autodrift/exact_post_ppo_repair.py
```

The residual is:

```text
L_conflict =
  preferred_branch_action_anchor
+ lambda_current_family_conflict_rejected * rejected_branch_boundary_anchor
```

It is a proposal-side guardrail only. M267/M264 closed-loop replay remains the
authoritative proof gate.

## Export Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.current_family_conflict_corpus \
  --checkpoint runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt \
  --boundary-corpus-npz runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz \
  --boundary-corpus-csv runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --row-ids 15,6 \
  --margin-replay-csv runs/m385_micro_a0_00075_m267_m264_first_replay/boundary_replay_rows.csv \
  --margin-policy m385micro_a0_00075 \
  --margin-floor 0.0001 \
  --max-weight 20 \
  --device cpu \
  --run-dir runs/m389_m267_row15_conflict_corpus
```

Result:

| Metric | Value |
| --- | ---: |
| rows | 2 |
| weight sum | 0.269177426 |
| boundary margin min | -0.000059669 |
| boundary margin max | -0.000001064 |
| actor inputs changed | false |
| PPO or actor update run | false |

## No-Update Smoke

The no-update exact-repair smoke verifies that the optional corpus is readable
and that all loss summaries include conflict terms.

```text
runs/m389_current_family_conflict_no_update_smoke/summary.json
```

| Metric | Value |
| --- | ---: |
| exact lexicographic pass | true |
| current-family conflict rows | 2 |
| conflict loss | 3.832874e-15 |
| preferred loss | 1.456967e-15 |
| rejected loss | 1.187954e-15 |
| exact M297 delta | 0 |
| exact M270 delta | 0 |

The loss is near zero because the anchors were exported from the same base
checkpoint used by the no-update run.

## Boundary Signal Check

M389 also evaluates the first failing M267/M264 boundary alpha as a zero-step
raw checkpoint:

```text
runs/m389_conflict_alpha001_signal_check/summary.json
```

| Metric | Value |
| --- | ---: |
| raw checkpoint | `runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_001.pt` |
| exact lexicographic pass | true |
| conflict loss | 3.564317e-11 |
| preferred loss | 1.191711e-11 |
| rejected loss | 1.186303e-11 |
| exact M297 delta | -0.000003815 |
| exact M270 delta | -0.000002384 |

The conflict residual is nonzero on alpha `0.001`, but the action drift is very
small, so the scalar signal is tiny. The next repair probe should not rely on
this exact loss alone; it must still run M267/M264 replay first.

## Tests

Focused test command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_current_family_conflict_corpus.py \
  tests/test_exact_post_ppo_repair.py \
  tests/test_old_key_recovery_targets.py \
  tests/test_old_key_preference_corpus.py
```

Result:

```text
26 passed in 1.08s
```

## Interpretation

M389 completes the infrastructure needed for the next no-PPO proof probe:

- row15 and row6 are now explicit current-family wrong-history boundary rows;
- exact repair can load and report the residual without changing actor inputs;
- the no-update path is stable;
- alpha `0.001` shows the residual has a detectable but small action-space
  signal;
- no driver checkpoint is promoted.

Because the signal is tiny, M390 should test a bounded repair direction with a
strict gate order: exact objectives first, then M267/M264 first replay, then
cumulative old-key replay, source-diverse proof, and M183/M170 first replay.

## Decision

Admit:

```text
m390-m267-conflict-residual-repair-probe
```

Decision:

```text
admit_m390_m267_conflict_residual_repair_probe
```
