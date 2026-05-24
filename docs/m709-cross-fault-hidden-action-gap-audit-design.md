# M709 Cross-Fault Hidden-Action Gap Audit Design

## Purpose

M709 designs the no-training audit required by M708.

M707 showed that cross-fault wrong histories do not create action or margin
gaps:

```text
wrong action gap >= 0.015: 0 / 2048
wrong margin gap >= 0.02:  0 / 2048
```

But reset-hidden often changes the first action:

```text
reset action gap >= 0.015: 2014 / 2048
reset margin gap >= 0.02:    11 / 2048
```

The next question is not "can we train from this corpus?" The next question is:

```text
where does the cross-fault wrong-history signal disappear?
```

This milestone is design-only:

```text
no implementation
no actor update
no optimizer
no PPO
no checkpoint promotion
no actor-input change
```

## Diagnostic Ladder

M710 should measure the same preferred current observation under three hidden
states:

```text
normal:
  preferred observation + preferred hidden

wrong_history:
  preferred observation + matched cross-fault hidden

reset_hidden:
  preferred observation + zero hidden
```

For each pair, measure:

```text
raw_hidden_l2:
  ||h_preferred - h_variant||

next_hidden_l2:
  ||GRU(response_obs, h_preferred) - GRU(response_obs, h_variant)||

fused_feature_l2:
  ||fusion(next_hidden_preferred, context) -
    fusion(next_hidden_variant, context)||

action_l2:
  ||tanh(actor_mean(fused_preferred)) -
    tanh(actor_mean(fused_variant))||

margin_gap:
  normal continuation margin - variant continuation margin
```

Use the already exposed actor path:

```text
model.recurrent_features_tensor(obs, hidden)
model.actor_mean(features)
```

This keeps the audit observational. It must not add new deployed actor
features, change actor behavior, or use hidden fault labels as actor inputs.

## Required Artifact Rows

M710 should write one row per pair and variant:

```text
pair_id
variant                         normal_vs_wrong_history | normal_vs_reset_hidden
seed
step
preferred_fault_family
preferred_fault_severity
wrong_fault_family
wrong_fault_severity
pairing_rule
assigned_split
normal_margin
variant_margin
margin_gap
success_drop
raw_hidden_l2
next_hidden_l2
fused_feature_l2
action_l2
raw_to_next_retention
raw_to_fused_retention
feature_to_action_retention
```

Also write grouped summaries:

```text
variant_summary.csv
fault_family_pair_variant_summary.csv
sentinel_summary.csv
```

Sentinel rows should be the M707 reset-only front/steering or front/combined
rows:

```text
front_lateral_authority_drop -> steering_fault
front_lateral_authority_drop -> combined_fault
steering_fault -> front_lateral_authority_drop
combined_fault -> front_lateral_authority_drop
```

These rows are diagnostics only. They do not become source-positive training
rows unless wrong-history action or margin gaps become meaningful.

## Result Classes

M710 should classify:

```text
raw_hidden_collapse:
  wrong raw_hidden_l2 is near zero, so matched cross-fault histories are not
  actually different recurrent states.

fusion_washout:
  wrong raw/next hidden gaps exist but fused_feature_l2 or action_l2 collapses.

action_washout:
  wrong fused_feature_l2 exists but action_l2 remains below threshold.

outcome_insensitive:
  wrong action_l2 exists but margin/success does not change.

reset_disruption_only:
  reset gaps are large but wrong-history gaps remain small at all deployed
  actor boundaries.

history_incompatibility_positive:
  wrong-history raw/feature/action gaps are nontrivial and paired with
  meaningful margin or success degradation.
```

M710 is still no-training. Only `history_incompatibility_positive` can admit a
new source-corpus design milestone. All other result classes should lead to an
audit or a design pivot.

## Thresholds

Pre-register these diagnostic thresholds:

```text
min_wrong_raw_hidden_l2:       0.05
min_wrong_fused_feature_l2:    0.01
min_wrong_action_l2:           0.015
min_wrong_margin_gap:          0.02
min_positive_rows:             30
min_unique_fault_pairs:         4
```

These are diagnostic thresholds, not promotion thresholds. They should not be
relaxed after seeing M710 results.

## Expected Interpretations

If M710 finds:

```text
wrong raw_hidden_l2 near zero
```

then M707's pairing is not creating incompatible histories at the recurrent
state level. The next branch should design stronger warm-up, active probing, or
fault schedules before the obstacle.

If M710 finds:

```text
wrong raw/next hidden gap exists but fused/action gap collapses
```

then the blocker is the response/context fusion or actor head. The next branch
should revisit architecture/objective, not scenario sampling.

If M710 finds:

```text
wrong action gap exists but margin does not change
```

then scenario states are not terminal-boundary sensitive enough. The next
branch should refine boundary sampling around the discovered action-divergent
fault pairs.

If M710 finds:

```text
reset gaps dominate and wrong gaps are small everywhere
```

then M707/M710 should be treated as reset-disruption evidence only. Source
export, PPO, and promotion remain blocked.

## Command Design

M710 should implement a command like:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.cross_fault_hidden_action_gap_audit \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/cross_fault_hidden_condition_scenarios.json \
  --seed-start 41000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m710_cross_fault_hidden_action_gap_audit
```

It should reuse M707's cross-fault matching rules and replay logic so that
results remain comparable.

## Required M710 Artifacts

```text
runs/m710_cross_fault_hidden_action_gap_audit/summary.json
runs/m710_cross_fault_hidden_action_gap_audit/row_hidden_action_gaps.csv
runs/m710_cross_fault_hidden_action_gap_audit/variant_summary.csv
runs/m710_cross_fault_hidden_action_gap_audit/fault_family_pair_variant_summary.csv
runs/m710_cross_fault_hidden_action_gap_audit/sentinel_summary.csv
docs/m710-cross-fault-hidden-action-gap-audit-implementation.md
```

## Decision

M709 admits:

```text
m710-cross-fault-hidden-action-gap-audit-implementation
```

M709 does not admit:

```text
source export
actor update
PPO
checkpoint promotion
actor input changes
```
