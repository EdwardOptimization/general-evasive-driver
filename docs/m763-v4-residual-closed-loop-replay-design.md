# M763 V4 Residual Closed-Loop Replay Design

## Purpose

M763 designs the first closed-loop replay test for the M761 residual head.

The question is:

```text
Do M761's exact first-action residual gains survive closed-loop rollout, or are
they only public objective-corpus artifacts?
```

This milestone is design-only:

```text
no actor training
no residual retraining
no PPO
no checkpoint promotion
no actor-input change
```

## Why This Design Is Needed

M761 proved that a frozen-backbone residual head can improve exact
normal-vs-intervention first-action metrics on the M755/M758 v4 corpus.
M762 audited that as a clean objective-only positive.

That still leaves the important open question:

```text
Does the residual head preserve normal closed-loop behavior while making the
wrong / ablated history branch remain behaviorally different under rollout?
```

M763 therefore separates three concepts:

```text
exact objective improvement:
  already shown by M761

closed-loop mechanism evidence:
  not yet tested

driver promotion:
  still blocked
```

## Inputs

M764 should use:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
runs/m761_v4_sequence_objective_probe/summary.json
runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_scenarios.json
```

The M755 rows remain an index/evidence corpus. M764 must reconstruct source
snapshots by replaying seed/fault/step metadata, as M758 and M761 did.

## Residual Policy Wrapper

M764 should not mutate the base actor. Instead, implement a wrapper:

```text
features, next_hidden = base_actor.recurrent_features_tensor(obs, hidden)
base_action = tanh(base_actor.actor_mean(features))
delta_action = residual_head(features)
executed_action = clip(base_action + alpha * delta_action, -1, 1)
```

Required checks:

```text
residual_head feature_dim matches actor feature_dim
base actor checksum is unchanged before and after replay
residual_head state is loaded eval-only
no optimizer is created
ppo_used == false
promoted == false
```

## Alpha Set

M764 should compare:

```text
alpha 0.0: base actor, no residual
alpha 0.2: first conservative passing M761 alpha
alpha 0.5: middle passing alpha
alpha 1.0: largest passing alpha, near-zero exact gap deficit
```

No alpha may be selected for promotion in M764.

## Replay Branches

For each source row, M764 should run:

```text
normal branch:
  normal observation and recurrent hidden

intervention branch:
  same row's M755/M761 intervention variant and horizon
```

Initial supported variants:

```text
zero_command_obs
reset_hidden_each_step
```

The implementation may support additional sequence variants if they are already
implemented locally, but it must report which variants were actually present.

For each alpha, run both branches from the same reconstructed source snapshot.
For `alpha=0.0`, this is the base closed-loop reference. For residual alphas,
the same wrapper is applied at every rollout step.

## Metrics

M764 should write:

```text
runs/m764_v4_residual_closed_loop_replay/summary.json
runs/m764_v4_residual_closed_loop_replay/alpha_metrics.csv
runs/m764_v4_residual_closed_loop_replay/replay_rows.csv
runs/m764_v4_residual_closed_loop_replay/objective_rows.csv
runs/m764_v4_residual_closed_loop_replay/rejected_rows.csv
```

Per replay row:

```text
contrast_group_id
source_index
seed
step
preferred_fault
preferred_fault_family
wrong_fault_family
fault_family_pair
variant
horizon
claim_boundary_level
alpha
branch
success
collision
off_road
spin_out
terminal_reason
return
steps
min_clearance_margin
min_obstacle_clearance
beta_abs_peak
first_steer
first_throttle
first_brake
prefix_l2_mean
prefix_l2_max
trajectory_l2_mean
trajectory_l2_max
```

Per alpha summary:

```text
normal_success_rate
normal_collision_rate
normal_margin_mean
normal_margin_regression_mean_vs_base
normal_margin_regression_p95_vs_base
normal_first_action_drift_mean_vs_base
normal_first_action_drift_p95_vs_base
intervention_success_rate
intervention_margin_mean
normal_minus_intervention_margin_gap_mean
normal_minus_intervention_success_gap
intervention_action_gap_mean_vs_normal
intervention_action_gap_p10_vs_normal
outcome_sensitivity_retention_rate
variant_stratified_metrics
horizon_stratified_metrics
fault_family_stratified_metrics
hard_negative_available_fraction
sentinel_false_positive_rate_if_available
```

## Candidate Gates

A closed-loop residual alpha can only be marked `closed_loop_replay_candidate`
if all of the following hold:

```text
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
actor_backbone_changed == false
optimizer_started == false
ppo_used == false
promoted == false

normal_success_rate >= base_normal_success_rate - 0.01
normal_collision_rate <= base_normal_collision_rate + 0.01
normal_margin_regression_mean_vs_base <= 0.01
normal_first_action_drift_mean_vs_base <= 0.004
normal_first_action_drift_p95_vs_base <= 0.012

intervention_action_gap_mean_vs_normal >= base_intervention_action_gap_mean + 0.003
intervention_action_gap_p10_vs_normal >= base_intervention_action_gap_p10
normal_minus_intervention_margin_gap_mean >= base_margin_gap_mean
outcome_sensitivity_retention_rate >= 0.95
```

These gates are intentionally conservative. M764 is not a promotion gate; it is
a mechanism replay gate.

## Result Classes

M764 should classify results as:

```text
v4_residual_closed_loop_replay_candidate:
  at least one nonzero alpha passes normal retention and closed-loop
  intervention sensitivity gates

v4_residual_closed_loop_replay_normal_regression:
  exact objective gains exist but residual rollout hurts normal behavior

v4_residual_closed_loop_replay_no_closed_loop_gap:
  normal behavior is retained but intervention/action/outcome gap does not
  survive rollout

v4_residual_closed_loop_replay_reconstruction_blocked:
  source snapshot reconstruction fails

v4_residual_closed_loop_replay_metadata_artifact:
  metadata, checksum, optimizer, PPO, or promotion guard fails
```

## Stratification Requirements

M764 must not rely only on aggregate metrics.

Required stratifications:

```text
variant:
  zero_command_obs
  reset_hidden_each_step

horizon:
  2
  4
  6
  8

preferred_fault_family
wrong_fault_family
fault_family_pair
source seed
claim_boundary_level
hard-negative availability
```

If a candidate only passes because the dominant `zero_command_obs` / long
horizon subgroup improves, M764 should still report the result but the follow-up
audit should classify the risk explicitly.

## Stop Rules

M764 must stop and write a clean negative or blocker if:

```text
reconstruction success rate < 0.98
normal branch has broad collision/margin regression
nonzero alphas fail to increase closed-loop action/outcome gaps
base actor checksum changes
an optimizer or PPO path is invoked
```

Do not repair or retune the residual head inside M764. If replay fails, M765
should audit the failure and choose between objective redesign, source refresh,
or a capped replay rerun.

## Next Step

Decision:

```text
admit_m764_v4_residual_closed_loop_replay_implementation
```

M764 should implement the no-PPO evaluator exactly as above. PPO and checkpoint
promotion remain blocked.
