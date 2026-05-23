# M465 Targeted Wrong-History Outcome Probe

## Purpose

M465 evaluates the M464 targeted pair surface with action and continuation
outcome gates. It explicitly separates wrong-history evidence from
reset/zero-current diagnostics.

No training, PPO, checkpoint update, actor-input change, or checkpoint
promotion is performed.

## Inputs

```text
checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
config:     configs/m457_history_necessity_late_reveal_zero_relvel.json
pairs:      runs/m464_wrong_history_targeted_pair_triage/targeted_pairs.csv
```

The M464 pair surface has `209` targeted pairs over `3` seed windows, `3`
labels, and `3` targets.

## Commands

Action intervention gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m464_wrong_history_targeted_pair_triage/targeted_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.05 \
  --max-pairs-per-checkpoint-target 80 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m465_targeted_wrong_history_action_gate
```

Outcome gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m464_wrong_history_targeted_pair_triage/targeted_pairs.csv \
  --delay-steps 2 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m465_targeted_wrong_history_outcome_gate
```

Selector/audit:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_critical_matched_current_selector \
  --pairs-csv runs/m464_wrong_history_targeted_pair_triage/targeted_pairs.csv \
  --action-interventions-csv runs/m465_targeted_wrong_history_action_gate/action_interventions.csv \
  --outcome-interventions-csv runs/m465_targeted_wrong_history_outcome_gate/outcome_interventions.csv \
  --max-pairs-per-checkpoint-target 80 \
  --min-margin-gap 0.02 \
  --min-action-distance 0.05 \
  --max-normal-pair-action-distance 0.08 \
  --min-target-z-delta 1.0 \
  --max-rows 128 \
  --max-per-probe-seed 32 \
  --max-per-target 48 \
  --max-per-variant 48 \
  --max-per-obstacle-bucket 12 \
  --min-accepted-rows 16 \
  --run-dir runs/m465_targeted_wrong_history_selector
```

## Results

Action gate:

```text
input pairs:             199
intervention rows:       995
```

Outcome gate:

```text
input pairs:             199
outcome rows:           1194
```

Selector:

```text
candidate rows:          995
action prefilter pass:   356
action-only rows:        322
outcome-critical rows:    95
accepted rows:            34
compact rows:             34
compact probe seeds:       3
compact labels:            3
compact targets:           3
compact variants:          3
selector_pass:          True
```

Accepted rows by variant:

```text
zero_current_response:    22
wrong_matched_history:     7
reset_hidden:              5
```

Wrong-history compact rows:

```text
compact rows:                         7
success-drop rows:                    0
collision-gap rows:                   0
obstacle-completion-drop rows:        0
positive-margin rows:                 7
labels:                               aes_feasible only
probe seeds:                          10300: 6, 10400: 1
targets:                              future_yaw_response: 4
                                      future_braking_deceleration: 3
normal margin range:                  3.548402 to 7.612638
max margin gap:                       0.055137
```

Artifacts:

```text
runs/m465_targeted_wrong_history_action_gate/summary.json
runs/m465_targeted_wrong_history_outcome_gate/summary.json
runs/m465_targeted_wrong_history_selector/summary.json
runs/m465_targeted_wrong_history_selector/wrong_history_evidence_audit.json
runs/m465_targeted_wrong_history_selector/wrong_history_accepted.csv
runs/m465_targeted_wrong_history_selector/wrong_history_compact.csv
```

## Interpretation

M465 improves over M462 in one narrow sense: wrong-history rows now enter the
compact corpus. However, they still do not support wrong-history proof
expansion. Every wrong-history compact row is `aes_feasible`, there are no
success-drop, collision-gap, or obstacle-completion-drop rows, and the normal
margin is high (`3.55 m` to `7.61 m`). These are high-slack margin-only rows,
not outcome-critical self-identification failures.

The targeted pair triage is useful as a mining step, but wrong-history proof
still needs a near-boundary condition. The next branch should filter or mine
for normal-history success with low terminal margin before asking whether wrong
history causes failure or near-failure.

## Decision

```text
targeted_probe_reject_wrong_history_gate_admit_m466
```

Do not expand wrong-history gates from M465. No checkpoint is promoted.
