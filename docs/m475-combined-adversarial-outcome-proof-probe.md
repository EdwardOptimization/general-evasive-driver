# M475 Combined Adversarial Outcome Proof Probe

## Purpose

M475 tests whether the source-diverse M474 adversarial wrong-history pair
surface contains near-boundary interventions that cause closed-loop outcome
degradation.

No training, PPO, actor-input change, proof gate expansion, or checkpoint
promotion is performed.

## Inputs

```text
pairs:      runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
config:     configs/m457_history_necessity_late_reveal_zero_relvel.json
```

M474 input summary:

```text
adversarial pairs:          197
near-boundary left states:   82
probe seeds:                  9
labels:                       2
targets:                      3
single seed share:     0.197970
single label share:    0.548223
```

## Commands

Action intervention gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv \
  --delay-steps 2 \
  --min-action-distance 0.05 \
  --max-pairs-per-checkpoint-target 160 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m475_combined_adversarial_action_gate
```

Outcome gate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m457_history_necessity_late_reveal_zero_relvel.json \
  --pairs-csv runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv \
  --delay-steps 2 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 160 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m475_combined_adversarial_outcome_gate
```

Outcome selector:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_critical_matched_current_selector \
  --pairs-csv runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv \
  --action-interventions-csv runs/m475_combined_adversarial_action_gate/action_interventions.csv \
  --outcome-interventions-csv runs/m475_combined_adversarial_outcome_gate/outcome_interventions.csv \
  --max-pairs-per-checkpoint-target 160 \
  --min-margin-gap 0.02 \
  --min-action-distance 0.05 \
  --max-normal-pair-action-distance 0.08 \
  --min-target-z-delta 1.0 \
  --max-rows 240 \
  --max-per-probe-seed 80 \
  --max-per-target 96 \
  --max-per-variant 96 \
  --max-per-obstacle-bucket 24 \
  --min-accepted-rows 16 \
  --run-dir runs/m475_combined_adversarial_outcome_selector
```

Near-boundary selector:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.near_boundary_wrong_history_selector \
  --candidates-csv runs/m475_combined_adversarial_outcome_selector/candidates.csv \
  --normal-margin-ceiling 0.75 \
  --min-margin-gap 0.02 \
  --min-return-gap-for-completion-drop 1.0 \
  --min-proof-rows 16 \
  --min-probe-seed-count 6 \
  --min-obstacle-label-count 2 \
  --min-target-count 2 \
  --min-success-or-collision-or-completion-rows 4 \
  --max-single-seed-share 0.50 \
  --max-single-label-share 0.70 \
  --run-dir runs/m475_combined_adversarial_near_boundary_selector
```

## Results

Action/outcome gates:

```text
input pairs:                   197
action intervention rows:      985
outcome intervention rows:    1182
```

Outcome selector:

```text
candidate rows:                985
action-prefilter pass:         297
outcome-critical rows:          85
accepted rows:                  28
compact rows:                   28
compact probe seeds:             7
compact labels:                  2
compact targets:                 2
compact variants: reset_hidden, zero_current_response
selector_pass:                True
```

The selector accepts reset/zero-current rows, not wrong-history rows:

```text
accepted_by_variant:
  reset_hidden:           5
  zero_current_response: 23
```

Near-boundary wrong-history selector:

```text
wrong-history rows:             197
near-boundary candidates:       197
proof candidates:                 0
near-boundary no-effect rows:   197
high-slack diagnostics:           0
wrong_history_gate_pass:      False
```

By label:

```text
drift_required: 89
unavoidable:   108
```

## Wrong-History Diagnostic

Wrong-history interventions are not action-null:

```text
wrong-history action distance mean:             0.053586
wrong-history action distance max:              0.151947
wrong-history action_prefilter pass rows:       131 / 197
wrong-history closer-to-right-action rows:      124 / 197
```

But they do not change closed-loop outcome:

```text
success-drop rows:               0
collision-gap rows:              0
obstacle-completion-drop rows:   0
positive-margin-gap rows:        0
margin gap mean:         -0.000467
margin gap max:           0.010044
```

Reset and zero-current interventions do cause outcome degradation on this same
surface. For example, reset/zero-current variants produce success drops on
lateral/yaw targets in the outcome summary, while wrong-history success rate
stays `1.0` for all three targets.

## Interpretation

M475 rejects wrong-history proof expansion. The M474 adversarial search fixed
source diversity and found stronger wrong histories, but those histories still
do not degrade closed-loop outcome. The policy appears to be sensitive to
current response and reset/zero-current ablations on the same surface, while
wrong matched history is either too weak, decays too quickly, or is corrected by
current observation feedback before terminal outcome changes.

This is an important negative result: the blocker is no longer source-diverse
pair availability. The blocker is that wrong-history action perturbations do
not translate into terminal-margin or success degradation.

## Decision

```text
combined_adversarial_outcome_probe_reject_proof_admit_m476
```

M476 should audit the no-effect mechanism before designing another search or
task family.

No checkpoint is promoted.
