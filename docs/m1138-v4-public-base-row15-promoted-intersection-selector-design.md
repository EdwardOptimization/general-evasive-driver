# M1138 V4 Public Base Row15 Promoted Intersection Selector Design

## Purpose

M1138 designs a deterministic family-intersection selector over the M1136
cross-family replay-calibrated rows.

This milestone is design-only. It does not run the selector, replay, objective
optimization, actor training, PPO, promotion, private holdout, or actor-input
changes.

## Motivation

M1136 showed that the M1134 aggregate rows preserve the proof relation under
their own source policies:

```text
source rows: 172
normal successes: 172
wrong-history successes: 0
success drops: 172
```

M1137 showed that direct mixed-family objective optimization is unsafe because
there are `34` failed duplicate geometry groups. But it also found a broad
all-policy intersection:

```text
all-policy pass rows: 148
physical pairs: 13
left steps: 6
targets: 2
max pair fraction: 0.135135
```

Therefore M1139 should select only rows that preserve normal-history success
and wrong-history failure across all five family policies before any objective
conversion.

## Inputs

```text
runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv
runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv
```

The selector must read existing replay artifacts only. It must not run replay.

## Policy Family

```text
row15_current
previous_m1078_base
short61049
short61050
short61051
```

Fail closed if any expected policy is missing from replay results for a
candidate row.

## Keep Rule

For each `family_row_id`, keep the row only if every expected policy has:

```text
normal_success == true
wrong_history_success == false
success_drop == true
normal_margin finite
wrong_history_margin finite
margin_gap finite
```

Rows failing any policy are written to a drop report with failed policy labels
and failure reasons.

## M1139 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.family_aggregate_intersection_selector \
  --family-rows-csv runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv \
  --cross-family-replay-rows-csv runs/m1136_row15_promoted_family_aggregate_replay_sanity/cross_family_replay_rows.csv \
  --expected-policy row15_current \
  --expected-policy previous_m1078_base \
  --expected-policy short61049 \
  --expected-policy short61050 \
  --expected-policy short61051 \
  --min-rows 100 \
  --min-physical-pairs 12 \
  --min-source-labels 4 \
  --min-targets 2 \
  --min-left-steps 6 \
  --max-physical-pair-fraction 0.25 \
  --max-source-label-fraction 0.45 \
  --run-dir runs/m1139_row15_promoted_intersection_selector
```

## Acceptance Criteria

M1139 passes only if:

```text
family_intersection_rows >= 100
physical_pairs >= 12
source_labels >= 4
targets >= 2
left_steps >= 6
max_physical_pair_fraction <= 0.25
max_source_label_fraction <= 0.45
all expected policies are present for every kept row
family_intersection_rows.csv exists
dropped_cross_family_rows.csv exists
policy_pass_matrix.csv exists
source_summary.csv exists
target_summary.csv exists
summary.json exists
training_started == false
ppo_used == false
replay_started == false
objective_optimization_started == false
promoted == false
private_holdout_used == false
```

The `targets >= 2` threshold is deliberate. M1137 showed that the all-policy
intersection loses lateral-accel rows but retains braking and yaw rows. The
selector must report this loss rather than pretending the full three-target
surface survived.

## Next If M1139 Passes

After selector pass, the next branch should design target-policy
materialization under the current public-gate base, not direct mixed-family
objective optimization. The objective corpus should use one hidden-state space.

## Decision

```text
row15_promoted_intersection_selector_design_admit_m1139_run
```

Next:

```text
m1139-v4-public-base-row15-promoted-intersection-selector
```
