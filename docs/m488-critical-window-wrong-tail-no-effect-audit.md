# M488 Critical-Window Wrong-Tail No-Effect Audit

## Purpose

M488 audits why M487 tail-aligned one-shot wrong-history interventions remain
mostly no-effect while reset-tail and zero-current controls degrade outcomes.

No training, PPO, actor-input change, checkpoint update, proof expansion, or
checkpoint promotion is performed.

## Inputs

```text
runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv
runs/m487_critical_window_tail_aligned_outcome_summary/variant_summary.csv
runs/m487_critical_window_tail_aligned_outcome_summary/combined_summary.json
```

Audit artifacts:

```text
runs/m488_critical_window_wrong_tail_no_effect_audit/summary.json
runs/m488_critical_window_wrong_tail_no_effect_audit/variant_mechanism_comparison.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_action_distance_bin.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_trajectory_distance_bin.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_normal_margin_bin.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_config.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_label.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_target.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_by_offset.csv
runs/m488_critical_window_wrong_tail_no_effect_audit/wrong_tail_proof_rows.csv
```

## Main Finding

Wrong-tail hidden injection is not ignored, but it is far weaker than the
controls and does not persist into outcome-relevant trajectory deviation.

```text
variant            rows  proof  events  first_action_mean  traj_mean  margin_gap_max
normal_tail        1080      0       0          0.000000   0.000000        0.000000
wrong_tail_once    1080     11       0          0.078874   0.068261        0.056394
reset_tail         1080    182      14          0.930876   1.015227        0.209951
zero_current_tail  1080    151      27          0.121885   0.458910        0.505877
```

Ratios:

```text
wrong_tail trajectory mean / reset_tail trajectory mean:       0.067238
wrong_tail trajectory mean / zero_current trajectory mean:     0.148747
wrong_tail first-action mean / reset_tail first-action mean:   0.084730
wrong_tail first-action mean / zero_current first-action mean: 0.647112
```

This separates two effects:

```text
wrong-tail first actions can move, but the closed-loop trajectory corrects quickly;
reset and zero-current create much larger sustained deviations and event rows.
```

## High-Perturbation Rows

Increasing a simple action-distance threshold is not enough:

```text
wrong_tail first_action_distance > 0.10:
  rows:         319
  proof rows:     8
  event rows:     0
  max gap: 0.056394

wrong_tail trajectory_mean > 0.10:
  rows:         261
  proof rows:     3
  event rows:     0
  max gap: 0.056394
```

The stronger wrong-tail rows still do not create success, collision, or
completion degradation.

## Source Shape

Wrong-tail proof rows are source-narrow in outcome meaning:

```text
proof rows:      11
event rows:       0
unique pairs:     6
normal-success proof rows: 8
normal-failure proof rows: 3
```

By config:

```text
late_high_energy: 9
near_threshold:   2
```

By label:

```text
unavoidable:    10
drift_required:  1
```

By target:

```text
future_braking_deceleration: 8
future_yaw_response:        3
future_lateral_accel:       0
```

By offset:

```text
4:  1
8:  2
12: 4
16: 4
```

The `future_lateral_accel_response` target has the largest wrong-tail
trajectory distance mean (`0.129232`) but zero proof rows. This is evidence
that M486 target scores are not yet outcome-aligned.

## Normal-Margin Audit

The no-effect result is not only high terminal slack:

```text
normal_margin bin  rows  proof  events  margin_gap_max
<=0                 122      3       0        0.056394
0-0.05                9      0       0        0.000123
0.05-0.10            12      0       0        0.000079
0.10-0.25             8      0       0        0.008763
0.25-0.50            60      2       0        0.025104
>0.50               869      6       0        0.044111
```

Some proof rows are already normal-history failures, so they are diagnostic
margin rows rather than clean self-ID proof. Low positive-margin rows remain
mostly no-effect.

## Interpretation

Dominant mechanism:

```text
tail_aligned_wrong_history_is_real_but_too_weak_or_too_quickly_corrected_and_m486_target_scores_are_not_outcome_aligned
```

M487 did not fail because the critical-window task is insensitive. The same
tail states show many reset and zero-current proof/event rows. It failed
because one-shot wrong-tail hidden injection does not create enough sustained
wrong action sequence to cross terminal outcome boundaries.

This argues against:

```text
just increasing target_z_delta;
just raising first_action_distance threshold;
claiming reset/zero-current rows as wrong-history proof;
training before mechanism separation.
```

The next diagnostic should answer:

```text
If we force the short wrong-tail action sequence for K steps, does the left
episode degrade?
```

If yes, the blocker is quick recurrent correction after a real wrong-belief
action proposal. If no, the pair/task surface is still not outcome-sensitive
enough and should be redesigned.

## Decision

```text
wrong_tail_no_effect_audit_admit_m489_tail_action_sequence_amplification_design
```

M489 should design a no-training diagnostic gate that compares:

```text
wrong_tail_once
wrong_tail_action_replay_K
wrong_tail_hidden_hold_K
reset_tail
zero_current_tail
```

for short horizons such as `K = 2, 4, 8, 12`. The goal is to separate
quick-correction from non-outcome-sensitive pair selection before any new
training objective or proof-surface expansion.

No checkpoint is promoted.
