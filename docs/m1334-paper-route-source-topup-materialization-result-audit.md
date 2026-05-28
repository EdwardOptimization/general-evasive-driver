# M1334 Paper-Route Source Top-Up Materialization Result Audit

## Summary

M1334 audits M1333 and synthesizes the source-repair top-up branch.

Decision:

```text
source_topup_materialization_audit_promote_to_materialized_objective_corpus_branch
```

The branch should close:

```text
paper_route_source_repair_topup_generation
```

The next branch should open:

```text
paper_route_materialized_source_history_objective_corpus
```

Route:

```text
Design an active materialized source-history objective corpus from the
history-distinguishable non-halfshaft M1333 rows, while quarantining halfshaft
rows until a drive-sensitive history probe is designed.
```

No training, PPO, promotion, private holdout, actor-input expansion, threshold
relaxation, or closed-loop self-identification claim occurs in M1334.

## M1333 Structural Audit

M1333 passed the structural materialization gate:

```text
result_class: source_topup_response_history_materialization_pass
source_pair_rows: 366
history_prefix_rows: 1464
history_frame_rows: 35136
history_intervention_rows: 1464
wrong_history_pair_rows: 1464
scenario_lookup_missing_count: 0
fault_lookup_missing_count: 0
plan_lookup_missing_count: 0
source_identity_duplicate_count: 0
source_identity_metadata_preserved: true
wrong_history_valid_count: 1464
```

Actor-view history is clean:

```text
actor_view_history_column_count: 12
actor_view_history_all_finite: true
forbidden_actor_view_history_columns: []
```

The canonical actor-view history columns are:

```text
vx
vy
yaw_rate
ax
ay
steer_state
steer_rate
drive_state
brake_state
prev_cmd_steer
prev_cmd_throttle
prev_cmd_brake
```

Source identity is preserved through the materialized artifacts:

```text
source_run_id
source_row_id
original_pair_id
source_identity
```

## Response Distinguishability

All-family diagnostics:

```text
response_l2_mean: 0.3003082731
response_l2_min: 0.0
response_l2_ge_0_01_count: 1376 / 1464
final_yaw_rate_diff_ge_0_01_count: 1300 / 1464
final_vy_diff_ge_0_01_count: 1280 / 1464
```

The zero-response rows are concentrated:

```text
zero response_l2 prefixes: 88
zero response_l2 source family: halfshaft_torque_loss->halfshaft_torque_loss
```

Interpretation:

```text
The current left/right brake probes are not drive-sensitive. They use
throttle=-1.0 and brake=+1.0, so a rear halfshaft torque-loss branch produces
no measurable command-response distinction during the history prefix.
```

This is a probe-design limitation, not an actor result and not a reason to
discard the clean non-halfshaft materialized corpus.

## Active Non-Halfshaft Subset

If halfshaft rows are quarantined, the active materialized subset remains broad:

```text
source pairs: 344
pair-probe groups: 688
history prefixes: 1376
source families: 6
zero response_l2 prefixes: 0
response_l2_ge_0_01_count: 1376 / 1376
```

Family counts:

```text
steering_actuator_fault: 96
single_wheel_grip_collapse: 64
single_wheel_brake_pull: 62
load_cg_perturbation: 54
left_right_split_mu: 37
tire_blowout_like: 31
```

Fold balance remains acceptable:

```text
fold 0: 71 pairs, 6 families, top share 0.2254
fold 1: 70 pairs, 6 families, top share 0.2857
fold 2: 68 pairs, 6 families, top share 0.2941
fold 3: 68 pairs, 6 families, top share 0.2941
fold 4: 67 pairs, 6 families, top share 0.2985
```

This exceeds the earlier `240` pair and `480` pair-probe group targets even
after halfshaft quarantine.

## Branch Evidence Summary

M1325 designed a targeted top-up source generation pass for undercovered
families.

M1326 implemented `source_topup_v1`, but the 9-step smoke was invalid because
all rollouts ended by horizon.

M1327 reran the same profile with 72 steps and produced `150` accepted rows. It
was source-positive but not a standalone replacement for M1322.

M1328 audited M1327 as additive top-up evidence over M1322.

M1329 designed source-run-identified additive merge/export.

M1330 exported a clean merged source corpus with:

```text
merged_source_identity_rows: 366
source_identity_duplicate_count: 0
semantic_duplicate_group_count: 0
family_balanced_rows: 250
accepted_fault_family_pairs: 7
```

M1331 planned the merged corpus:

```text
planned_source_pairs: 366
planned_pair_probe_groups: 732
max_source_family_fold_share: 0.2739726027
materialized_source_pair_count: 0
```

M1332 designed a dedicated source-run identity preserving materializer.

M1333 implemented and ran it successfully, with the halfshaft probe-silence
diagnostic recorded rather than hidden.

## Supported Claims

Supported:

```text
The source-repair top-up branch produced a clean, source-identity-preserving,
materialized command-response history corpus.
```

Supported:

```text
After quarantining halfshaft, the active materialized subset remains broad
enough for the next source-history objective corpus design: 344 pairs, 688
groups, 6 families, and no zero-response prefixes.
```

Supported:

```text
Source-run-specific fault profiles and params_override handling are necessary
for materializing the merged corpus.
```

## Falsified Or Unsupported Claims

Falsified:

```text
The current brake/lift history probes make halfshaft torque-loss rows
history-distinguishable.
```

Still unsupported:

```text
global_friction_step source coverage;
halfshaft reaching the 30-row source target;
drive-sensitive halfshaft history materialization;
policy-side source-history objective improvement;
closed-loop PPO continuation;
promotion;
paper-level evidence;
strong self-identification.
```

## Failure Taxonomy

Primary taxonomy:

```text
scenario_sampling_failure
```

Reason:

```text
The failure is not a software/materialization failure. It is a probe/source
sampling limitation: halfshaft torque loss requires drive-sensitive history
commands, while the current prefixes are braking/lift probes.
```

Non-failures:

```text
proof_washout: no actor update was run
behavior_regression: no deployed policy was evaluated
contract_violation: actor-view history remains clean
training_instability: no training occurred
```

## Public-Gate Overfit Risk

Risk:

```text
medium
```

Reason:

```text
The materialized corpus is still built from public source-mining artifacts and
will be used for objective design. It should not be reported as private
generalization evidence.
```

Mitigation:

```text
The next branch must use source-identity splits, keep halfshaft/global-friction
quarantine explicit, and run objective changes through exact public gates before
any PPO or promotion.
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close:

```text
paper_route_source_repair_topup_generation
```

Open:

```text
paper_route_materialized_source_history_objective_corpus
```

Next milestone:

```text
m1335-paper-route-materialized-source-history-objective-corpus-design
```

Scope:

```text
Design an objective-corpus export around the active non-halfshaft M1333 subset;
write explicit quarantine artifacts for halfshaft and global friction;
do not train;
do not run PPO;
do not promote.
```

Backlog:

```text
Drive-sensitive halfshaft response-history probes should be designed later,
using positive throttle / coast / mixed drive prefixes instead of only
brake/lift prefixes.
```

## Guardrails

Guardrails held:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```
