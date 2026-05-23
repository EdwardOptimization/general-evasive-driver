# M480 Late Once Wrong-History Implementation

## Purpose

M480 implements the late one-shot wrong-history diagnostic variants designed in
M479 and reruns the persistent wrong-history intervention gate on the M474
source-diverse adversarial pair surface.

No training, PPO, actor-input change, checkpoint update, or checkpoint promotion
is performed.

## Implementation

Updated module:

```text
src/autodrift/persistent_wrong_history_intervention_gate.py
```

New diagnostic variants:

```text
wrong_late_2_once
wrong_late_4_once
wrong_late_8_once
wrong_late_12_once
```

Each late one-shot variant uses:

```text
family = wrong_late_once
hold_steps = 1
clamp_hidden = false
```

Focused tests:

```text
tests/test_persistent_wrong_history_intervention_gate.py
```

The existing clamped variants remain in the same run for comparison, but their
rows are kept separate from the late-one-shot proof decision.

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
  --run-dir runs/m480_late_once_wrong_history_intervention_gate
```

Artifacts:

```text
runs/m480_late_once_wrong_history_intervention_gate/summary.json
runs/m480_late_once_wrong_history_intervention_gate/late_once_summary.json
runs/m480_late_once_wrong_history_intervention_gate/persistent_outcomes.csv
runs/m480_late_once_wrong_history_intervention_gate/variant_summary.csv
```

## Overall Results

```text
input pairs:                 197
outcome rows:               2955
variant summary rows:         45
best variant:      wrong_hold_16
best proof rows:              25
best event rows:              10
best probe seeds:              6
best labels:                   2
best targets:                  2
best single seed share:     0.28
best single label share:    0.56
```

The strongest result remains the clamped persistent diagnostic:

```text
wrong_hold_16:
  proof-style rows: 25
  success/collision/completion rows: 10
  probe seeds: 6
  labels: 2
  targets: 2
```

## Late One-Shot Results

Late one-shot rows:

```text
late-once rows:                         788
late-once proof-style rows:              16
late-once success/collision/event rows:   0
late-once probe seeds:                    2
late-once labels:                         2
late-once targets:                        2
single-seed share:                    0.625
single-label share:                   0.625
```

By variant:

```text
wrong_late_12_once: 13
wrong_late_2_once:   1
wrong_late_4_once:   1
wrong_late_8_once:   1
```

By seed:

```text
10300:  6
10800: 10
```

By label:

```text
unavoidable:    10
drift_required:  6
```

By target:

```text
future_lateral_accel_response: 8
future_yaw_response:           8
```

The late one-shot result fails the M479 natural-late pass rule because it has no
success/collision/completion rows, uses only two probe seeds, and has
single-seed share above the source-diversity cap.

## Interpretation

M480 is not a full natural wrong-history proof. Late one-shot intervention
produces a real timing signal, but it is margin-only and source-narrow:

```text
wrong_once:        0 proof rows
wrong_late_*_once: 16 margin-only proof-style rows
wrong_hold_16:    25 proof rows, including 10 event rows
```

The result supports the M476/M478 diagnosis: wrong belief can matter, but a
single wrong hidden injection is often corrected before it changes closed-loop
success. Injecting it later helps, especially at `wrong_late_12_once`, but the
evidence is still not source-diverse event proof.

## Decision

```text
late_once_margin_only_source_narrow_admit_m481_critical_window_design
```

M481 should design a shorter or more critical emergency-window task/gate rather
than continue adding late-one-shot variants. The goal is to test whether a
natural one-shot or naturally persistent wrong belief becomes outcome-critical
when the actor has less recovery time after the wrong-history perturbation.

No checkpoint is promoted.
