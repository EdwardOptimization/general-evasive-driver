# M478 Persistent Wrong-History Intervention Implementation

## Purpose

M478 implements the diagnostic persistent/later wrong-history intervention gate
designed in M477 and runs a no-training smoke on the M474 adversarial pair
surface.

No training, PPO, actor-input change, checkpoint update, or checkpoint
promotion is performed.

## Implementation

New module:

```text
src/autodrift/persistent_wrong_history_intervention_gate.py
```

Focused tests:

```text
tests/test_persistent_wrong_history_intervention_gate.py
```

The module reuses M475 snapshot and rollout semantics, but adds diagnostic
hidden-state intervention variants:

```text
normal
wrong_once
wrong_hold_4
wrong_hold_8
wrong_hold_16
wrong_late_4_hold_4
wrong_late_8_hold_4
wrong_late_4_hold_8
wrong_reseed_4
reset_hidden
zero_current_response
```

These variants are diagnostic only. They do not change deployable actor inputs.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.persistent_wrong_history_intervention_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv \
  --delay-steps 2 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 160 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m478_persistent_wrong_history_intervention_gate
```

Artifacts:

```text
runs/m478_persistent_wrong_history_intervention_gate/summary.json
runs/m478_persistent_wrong_history_intervention_gate/persistent_outcomes.csv
runs/m478_persistent_wrong_history_intervention_gate/variant_summary.csv
```

## Results

```text
input pairs:                 197
outcome rows:               2167
variant summary rows:         33
best variant:      wrong_hold_16
best proof rows:              25
best event rows:              10
best probe seeds:              6
best labels:                   2
best targets:                  2
best single seed share:     0.28
best single label share:    0.56
```

Proof-style candidate rows across diagnostic wrong-history variants:

```text
wrong_hold_16:         25 proof rows, 10 event rows
wrong_late_4_hold_8:   19 proof rows,  4 event rows
wrong_late_8_hold_4:   17 proof rows,  4 event rows
wrong_hold_4:           1 proof row,   0 event rows
wrong_hold_8:           1 proof row,   0 event rows
wrong_late_4_hold_4:    1 proof row,   0 event rows
wrong_reseed_4:         1 proof row,   0 event rows
wrong_once:             0 proof rows
```

Combined proof-style diagnostic rows:

```text
total diagnostic proof rows: 65
probe seeds:                 6
labels:                      2
targets:                     2
```

By label:

```text
unavoidable:    42
drift_required: 23
```

By target:

```text
future_yaw_response:           33
future_lateral_accel_response: 32
```

## Interpretation

M478 confirms the M476 diagnosis. The hidden state can be causally
outcome-critical when the wrong belief is held active during the emergency
window:

```text
wrong_once:     0 proof rows
wrong_hold_16: 25 proof rows
```

Late held interventions also work:

```text
wrong_late_4_hold_8: 19 proof rows
wrong_late_8_hold_4: 17 proof rows
```

This is not deployable self-identification proof because the persistent/later
wrong hidden state is artificially clamped. It is a mechanism result: the
current one-shot wrong-history probe fails because the wrong hidden state is too
weak or too quickly corrected, not because hidden belief is irrelevant.

## Decision

```text
persistent_wrong_history_diagnostic_pass_admit_m479
```

M479 should design the least-artificial next diagnostic: late one-shot
wrong-history injection and/or a shorter emergency window, so the project can
separate "belief matters only if clamped" from "belief matters naturally when
wrong at the critical instant."

No checkpoint is promoted.
