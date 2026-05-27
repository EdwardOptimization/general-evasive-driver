# M1153 V4 Public Base Row15 Promoted Unsafe-Margin Projection Runner Implementation

## Purpose

M1153 implements the promoted unsafe-margin projection runner designed in
M1152. This is infrastructure only. It does not execute the projection
experiment, run first replay, train actor weights, run PPO, mine new rows,
promote a checkpoint, use private holdout, or change actor inputs.

## Implementation

New runner:

```text
src/autodrift/row15_promoted_unsafe_margin_projection_probe.py
```

The runner reuses existing project helpers for:

```text
checkpoint interpolation
allowed-parameter diff audit
actor-input signature audit
exact outcome-intervention objective evaluation
boundary-outcome replay
strict JSON/CSV artifact writing
```

It replaces the old M1123 hardcoded row15 logic with M1149 failed-row handling:

```text
input failed rows:
  --failed-rows-csv runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv

failed-row grouping:
  group by arbitrary surface label from the CSV

unsafe-margin screen:
  normal_success == true
  normal_margin >= 0.0
  wrong_history_success == false
  wrong_history_margin < 0.0
```

Default M1149 first-replay surfaces:

```text
m183_m168
m183_m170
m193_m189
m212_m204
m223_m219
m267_m264
current_m333_surface
m314_continuity_surface
m317_continuity_surface
row15_promoted_materialized
```

The runner exposes:

```text
python -m autodrift.row15_promoted_unsafe_margin_projection_probe --help
```

## Result Classes

The runner implements the M1152 result classes:

```text
row15_promoted_unsafe_margin_projection_no_candidate
row15_promoted_unsafe_margin_projection_first_replay_failed
row15_promoted_unsafe_margin_projection_first_replay_candidate
```

The runner always writes guardrail metadata:

```text
training_started: false
actor_training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
family_intersection_replay_started: false
full_public_gate_started: false
fresh_ood_started: false
behavior_gate_started: false
```

## Tests

New focused tests:

```text
tests/test_row15_promoted_unsafe_margin_projection_probe.py
```

Covered behavior:

```text
failed-row CSV validation
failed-row grouping by arbitrary surface labels
alpha pass classification requiring all failed rows and nonzero alpha
M1152 result-class mapping
M1149 ten-surface first-replay default scope
```

Validation commands run:

```text
python -m compileall -q src/autodrift/row15_promoted_unsafe_margin_projection_probe.py \
  tests/test_row15_promoted_unsafe_margin_projection_probe.py

PYTHONPATH=src python -m pytest -q \
  tests/test_row15_promoted_unsafe_margin_projection_probe.py

PYTHONPATH=src python -m autodrift.row15_promoted_unsafe_margin_projection_probe --help
```

Result:

```text
5 passed
```

## Guardrails

M1153 does not run the projection experiment. The `--help` smoke only verifies
CLI availability and does not load checkpoints or replay environments.

No actor training, PPO, full replay/projection evaluation, mining, promotion,
private holdout, or actor-input change occurred.

## Decision

```text
decision: row15_promoted_unsafe_margin_projection_runner_implemented_route_to_projection_run
next: m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run
```
