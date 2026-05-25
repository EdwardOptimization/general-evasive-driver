# M764 V4 Residual Closed-Loop Replay Implementation

## Purpose

M764 implements the no-PPO closed-loop replay evaluator designed in M763.

The question is:

```text
Do M761's exact first-action residual gains survive closed-loop rollout?
```

This milestone is diagnostic only:

```text
base actor frozen
residual head loaded eval-only
no optimizer
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M764 adds:

```text
src/autodrift/v4_residual_closed_loop_replay.py
tests/test_v4_residual_closed_loop_replay.py
```

The evaluator:

```text
loads the BC5660 recurrent actor;
loads the M761 residual head;
reconstructs M755 source snapshots from seed/fault/step metadata;
runs normal and intervention closed-loop branches;
compares alpha 0.0, 0.2, 0.5, and 1.0;
applies the residual wrapper at every rollout step;
writes replay rows, objective rows, alpha metrics, rejected rows, and summary.
```

Action wrapper:

```text
features, next_hidden = base_actor.recurrent_features_tensor(obs, hidden)
base_action = tanh(base_actor.actor_mean(features))
delta_action = residual_head(features)
executed_action = clip(base_action + alpha * delta_action, -1, 1)
```

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m764_v4_residual_closed_loop_replay \
  --device cpu \
  --alphas 0.0,0.2,0.5,1.0
```

Output:

```text
runs/m764_v4_residual_closed_loop_replay/summary.json
runs/m764_v4_residual_closed_loop_replay/alpha_metrics.csv
runs/m764_v4_residual_closed_loop_replay/replay_rows.csv
runs/m764_v4_residual_closed_loop_replay/objective_rows.csv
runs/m764_v4_residual_closed_loop_replay/rejected_rows.csv
runs/m764_v4_residual_closed_loop_replay/variant_gap_summary.csv
runs/m764_v4_residual_closed_loop_replay/horizon_gap_summary.csv
```

## Evidence Summary

Registered result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0

replay_rows: 9704
objective_rows: 4852
alphas:
  0.0
  0.2
  0.5
  1.0

candidate_alpha_count: 3
candidate_alphas:
  0.2
  0.5
  1.0

actor_backbone_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Actor checksum before and after:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Alpha Metrics

Base alpha:

```text
alpha 0.0:
  normal_success_rate: 1.000000
  intervention_success_rate: 1.000000
  intervention_action_gap_mean_vs_normal: 0.041716
  intervention_action_gap_p10_vs_normal: 0.026395
  normal_minus_intervention_margin_gap_mean: 0.028754
```

Residual alphas:

```text
alpha 0.2:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_margin_regression_mean_vs_base: 0.000165
  normal_first_action_drift_mean/p95_vs_base: 0.000480 / 0.000939
  intervention_action_gap_mean/p10_vs_normal: 0.047937 / 0.028594
  normal_minus_intervention_margin_gap_mean: 0.032770
  outcome_sensitivity_retention_rate: 1.000000
  closed_loop_replay_candidate: true

alpha 0.5:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_margin_regression_mean_vs_base: 0.000446
  normal_first_action_drift_mean/p95_vs_base: 0.001200 / 0.002348
  intervention_action_gap_mean/p10_vs_normal: 0.057721 / 0.031984
  normal_minus_intervention_margin_gap_mean: 0.039159
  intervention_success_rate: 0.999176
  intervention_collision_rate: 0.000824
  outcome_sensitivity_retention_rate: 1.000000
  closed_loop_replay_candidate: true

alpha 1.0:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_margin_regression_mean_vs_base: 0.001022
  normal_first_action_drift_mean/p95_vs_base: 0.002401 / 0.004697
  intervention_action_gap_mean/p10_vs_normal: 0.074868 / 0.038011
  normal_minus_intervention_margin_gap_mean: 0.050751
  intervention_success_rate: 0.996702
  intervention_collision_rate: 0.003298
  outcome_sensitivity_retention_rate: 1.000000
  closed_loop_replay_candidate: true
```

Alpha `0.2` is the conservative first passing closed-loop candidate. Alpha
`1.0` produces the strongest wrong/ablated-history sensitivity but also causes
`4/1213` intervention-branch collisions. Those collisions occur on the
intervention branch, not the normal driver branch.

## Stratification

Aggregate by intervention variant across alphas:

```text
reset_hidden_each_step:
  rows: 676
  intervention_prefix_l2_mean_mean: 0.030437
  p10/p95: 0.025250 / 0.038547

zero_command_obs:
  rows: 4176
  intervention_prefix_l2_mean_mean: 0.059628
  p10/p95: 0.043236 / 0.086205
```

Per-alpha variant mean gaps:

```text
alpha 0.0:
  reset_hidden_each_step: 0.025947
  zero_command_obs: 0.044269

alpha 0.2:
  reset_hidden_each_step: 0.027937
  zero_command_obs: 0.051174

alpha 0.5:
  reset_hidden_each_step: 0.031082
  zero_command_obs: 0.062033

alpha 1.0:
  reset_hidden_each_step: 0.036783
  zero_command_obs: 0.081033
```

The residual effect is present in both variants but remains stronger for
`zero_command_obs`, the dominant M755/M761 subgroup.

## Supported Claims

M764 supports:

```text
1. M761's exact residual signal survives closed-loop replay on the public
   M755/M761 corpus.

2. Normal closed-loop behavior is retained for all tested residual alphas:
   normal success is 1213/1213 and normal collision rate is 0.

3. Wrong/ablated-history intervention branches become more action-divergent
   and more margin-sensitive as alpha increases.

4. The broader v4 extreme/proxy coverage branch produced not only sequence
   outcome rows and exact objective signal, but also a closed-loop residual
   mechanism signal.
```

## Falsified Claims

M764 falsifies:

```text
1. M761's exact first-action gains disappear immediately under rollout.

2. Applying the residual head necessarily breaks normal closed-loop behavior
   on the registered public v4 corpus.

3. The v4 residual signal is only a reconstruction or actor-checksum artifact.
```

M764 does not prove:

```text
1. The residual head should be promoted into the driver.

2. PPO is safe.

3. The result generalizes beyond the public M755/M761 replay corpus.

4. Current proxy faults are true tire blowout, wheel lock, axle-break, or
   four-wheel vehicle physics.
```

## Failure Taxonomy Summary

Primary residual risk:

```text
scenario_sampling_failure
```

Reason:

```text
The replay is positive, but it is still evaluated on the public M755/M761
corpus. Hard-negative availability remains 0.721352, and the corpus is
dominated by zero_command_obs and long horizons.
```

Additional risks:

```text
public_gate_overfit_risk:
  M761 trained on this public objective corpus and M764 replays the same source
  family.

intervention_branch_aggression:
  alpha 1.0 produces 4/1213 intervention collisions. This supports mechanism
  sensitivity, but it should be audited before any deployment-like claim.
```

Not failures:

```text
not metadata_artifact
not reconstruction_blocked
not contract_violation
not proof_washout
not training_instability
not promotion_gate_failure
```

## Next Branch Decision

Decision:

```text
v4_residual_closed_loop_replay_candidate_admit_audit
```

M765 should audit:

```text
1. whether M764 is a clean closed-loop mechanism positive;
2. whether alpha 0.2 should be treated as the conservative replay candidate;
3. whether alpha 1.0's intervention-branch collisions are useful sensitivity
   evidence or too aggressive;
4. whether the next step should be source-holdout replay, a fresh v4 residual
   corpus, or residual objective redesign.
```

PPO and checkpoint promotion remain blocked.
