# M1272 Paper-Route Four-Wheel Source Viability Calibration Result Audit

## Summary

M1272 audits the M1271 calibrated four-wheel source-positive result.

Decision:

```text
four_wheel_source_viability_calibration_audit_admit_source_corpus_export
```

M1271 is a valid no-policy source-positive result:

```text
accepted_separable_pairs: 108
matched_pair_count: 720
accepted_fault_family_pairs: 3
result_class: capability_separable_signal
source_positive: true
```

But M1271 should not route directly to actor/Gym integration. The accepted rows
must first be exported into a stratified source corpus with boundary, high-regret,
and family-balanced subsets.

## Evidence

Primary artifacts:

```text
runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json
runs/m1271_four_wheel_source_viability_calibration_smoke/accepted_separable_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/matched_capability_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/action_rollouts.csv
```

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

Successful rollouts ended by obstacle completion:

```text
success_terminal_reason_counts:
  obstacle_completed: 3950
```

Horizon-only rows remain non-success.

## Source Diversity

Accepted rows by family:

```text
single_wheel_brake_pull->single_wheel_brake_pull: 59
left_right_split_mu->left_right_split_mu: 28
single_wheel_grip_collapse->single_wheel_grip_collapse: 21
halfshaft_torque_loss->halfshaft_torque_loss: 0
```

Accepted rows by speed:

```text
14.0: 41
15.0: 31
16.0: 36
```

Accepted rows by obstacle distance:

```text
12.0: 19
13.0: 16
14.0: 18
15.0: 31
16.0: 24
```

Accepted rows by obstacle half-width:

```text
0.55: 30
0.65: 31
0.75: 27
0.85: 20
```

Accepted rows by lateral offset:

```text
0.0: 96
-0.25: 6
0.25: 6
```

Unique accepted source geometries:

```text
unique scenario_ids: 71
unique geometry tuples: 71
```

Interpretation:

```text
not a single-row artifact;
not a single-speed artifact;
not a single-distance or single-width artifact;
not ready as a broad scenario distribution because lateral-offset coverage is
mostly centered and halfshaft is inactive.
```

## Boundary Usefulness

Accepted min own-branch margin distribution:

```text
min: 0.0313709343
p10: 0.1302419300
p25: 0.2867351457
median: 0.6499383280
p75: 1.3058268901
p90: 2.0079514963
max: 2.8468477019
```

Near-boundary counts:

```text
min own margin <= 0.05: 5
min own margin <= 0.10: 8
min own margin <= 0.20: 19
```

Accepted min cross-regret distribution:

```text
min: 0.0242185615
p10: 0.0331171035
p25: 0.0365576063
median: 0.0407149595
p75: 0.0530164222
p90: 0.1003316162
max: 0.5091632963
```

High-regret counts:

```text
min cross-regret >= 0.05: 32
min cross-regret >= 0.10: 11
min cross-regret >= 0.20: 4
min cross-regret >= 0.40: 2
```

Interpretation:

```text
M1271 contains real near-boundary material, but the full 108-row set is too easy
on average for immediate history/intervention claims.
```

The next source step should export boundary-stratified subsets instead of using
the full accepted set unfiltered.

## Family-Level Notes

`single_wheel_brake_pull` supplies the largest accepted set:

```text
n: 59
min own margin median: 1.2509893690
min cross-regret median: 0.0387094087
```

This family is useful for source diversity but many rows are margin-easy.

`left_right_split_mu` supplies centered, cleaner left/right action divergence:

```text
n: 28
min own margin median: 0.4505792022
min cross-regret median: 0.0411568429
accepted lateral offset: 0.0 only
```

This family should remain in the next corpus but needs boundary prioritization.

`single_wheel_grip_collapse` supplies the strongest regret and best boundary
rows:

```text
n: 21
min own margin median: 0.2262373566
min cross-regret median: 0.0914655412
min cross-regret max: 0.5091632963
accepted lateral offsets: -0.25, 0.0, 0.25
```

This family is the best immediate candidate for boundary/history intervention
experiments.

## Near-Boundary Rows

Representative near-boundary accepted rows:

```text
pair 22:
  family: single_wheel_grip_collapse
  speed=14, obstacle_x=12, y=0.0, half_width=0.65
  min own margin=0.0313709343
  min cross-regret=0.0648548436
  best_action_l2=1.5

pair 648:
  family: left_right_split_mu
  speed=16, obstacle_x=15, y=0.0, half_width=0.75
  min own margin=0.0319581757
  min cross-regret=0.0539167843
  best_action_l2=1.5

pair 10 / 42:
  family: single_wheel_grip_collapse
  speed=14, obstacle_x=12, y=-0.25 / 0.25, half_width=0.75
  min own margin=0.0365556645
  min cross-regret=0.0506736565
  best_action_l2=0.25
```

These rows are suitable for a future boundary source corpus because they retain
strict own-branch success while remaining close enough to the terminal margin
boundary.

## Halfshaft Inactivity

Halfshaft torque-loss rows:

```text
candidate rows: 180
accepted: 0
rejection_reason best_actions_too_close: 180
best_action_l2 max: 0.0
min_cross_regret max: 0.0
own_branch_viable: 180
```

Interpretation:

```text
halfshaft torque loss is viable but action-equivalent under the current brake
dominant source lattice.
```

Do not force halfshaft into the next accepted corpus. Either drop it from the
next source corpus or mine it later under a drive-torque / throttle-on phase
where halfshaft asymmetry can actually affect the action boundary.

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate M1271 rows directly into actor/Gym.

Admit one bounded no-training corpus export:

```text
m1273-paper-route-four-wheel-source-corpus-export
```

The export should produce:

```text
all_accepted_source_rows.csv
near_boundary_source_rows.csv
high_regret_source_rows.csv
family_balanced_source_rows.csv
inactive_fault_families.csv
summary.json
```

Recommended subset definitions:

```text
near_boundary:
  min(margin_A_best_A, margin_B_best_B) <= 0.20

high_regret:
  min(cross_regret_A, cross_regret_B) >= 0.05

family_balanced:
  cap each accepted family at 21 rows, sorted by boundary priority then regret

inactive family:
  no accepted rows and best_action_l2 max == 0.0
```

M1273 remains source-corpus infrastructure. It must not train, run PPO, promote,
expand actor inputs, use private holdout, or claim driver performance.
