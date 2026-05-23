# M497 Natural Belief Decision-Window Outcome Gate

## Purpose

M497 tests the M496 targeted natural belief pair surface with early
decision-window wrong-history outcome interventions.

No training, PPO, actor-input change, checkpoint update, or checkpoint
promotion is performed.

## Split

M496 targeted pairs were split by `config`:

```text
short_reveal:      116
warmup_capability: 178
```

Split artifacts:

```text
runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv
runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv
```

## Commands

Both splits were run with early decision-window offsets:

```text
tail_offsets: 0, 2, 4, 8
max_continuation_steps: 80
min_margin_gap: 0.02
max_pairs_per_checkpoint_target: 0
pair_label_mode: matching
```

Short-reveal command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_aligned_wrong_history_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m494_natural_belief_short_reveal_zero_relvel.json \
  --pairs-csv runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv \
  --tail-offsets 0,2,4,8 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m497_short_reveal_decision_window_gate
```

Warm-up capability command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.tail_aligned_wrong_history_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config configs/m494_natural_belief_warmup_capability_zero_relvel.json \
  --pairs-csv runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv \
  --tail-offsets 0,2,4,8 \
  --max-continuation-steps 80 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m497_warmup_capability_decision_window_gate
```

Combined artifacts:

```text
runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv
runs/m497_natural_belief_decision_window_outcome_summary/combined_summary.json
runs/m497_natural_belief_decision_window_outcome_summary/variant_summary.csv
```

## Per-Config Results

```text
short_reveal:
  input pairs:                   116
  valid tail pairs:              436
  invalid tail pairs:             28
  wrong_tail_once proof rows:      4
  wrong_tail_once event rows:      0
  best offset:                     0

warmup_capability:
  input pairs:                   178
  valid tail pairs:              688
  invalid tail pairs:             24
  wrong_tail_once proof rows:     11
  wrong_tail_once event rows:      0
  best offset:                     0
```

## Combined Wrong-Tail Results

```text
input pairs:                         294
valid tail pairs:                   1124
invalid tail pairs:                   52
wrong_tail_once proof rows:           15
wrong_tail_once event rows:            0
wrong_tail_once probe seeds:           3
wrong_tail_once labels:                2
wrong_tail_once targets:               2
wrong_tail_once configs:               2
single-seed share:              0.666667
single-label share:             0.533333
wrong-history event proof:          false
```

Wrong-tail proof rows by config:

```text
warmup_capability: 11
short_reveal:       4
```

Wrong-tail proof rows by offset:

```text
0: 4
2: 4
4: 3
8: 4
```

Wrong-tail proof rows by label:

```text
drift_required: 8
unavoidable:    7
```

Wrong-tail proof rows by target:

```text
future_yaw_response:           12
future_lateral_accel_response:  3
```

## Controls

The same decision-window rows are outcome-sensitive under stronger response
ablations:

```text
reset_tail / zero_current_tail proof rows: 472
reset_tail / zero_current_tail event rows:  17
```

By variant:

```text
reset_tail:        298
zero_current_tail: 174
```

By config:

```text
warmup_capability: 352
short_reveal:      120
```

## Interpretation

M497 is a negative wrong-history proof result and a positive control-sensitivity
diagnostic.

The natural belief decision-window tasks and selected pairs are not
outcome-insensitive in general: reset-hidden and zero-current-response controls
produce many proof candidates and `17` event rows. But the one-shot
wrong-history intervention still produces only `15` margin-only rows and `0`
event rows.

Classification:

```text
control_only_sensitivity
```

This means the blocker is not merely task triviality. The next step is to audit
whether wrong-history action and trajectory perturbations remain too weak,
whether proof rows are concentrated by seed/target, or whether the targeted
score is still not aligned with outcome-relevant action error.

## Decision

```text
natural_decision_window_gate_reject_wrong_history_event_proof_admit_m498_no_effect_audit
```

M498 should audit M497 action and trajectory distances for wrong-history rows
against reset/zero-current controls before changing the task, intervention, or
training objective.

No checkpoint is promoted.
