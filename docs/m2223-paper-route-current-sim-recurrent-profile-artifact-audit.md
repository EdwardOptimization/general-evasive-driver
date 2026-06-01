# M2223 Paper-Route Current-Sim Recurrent Profile Artifact Audit

- status: completed
- decision: `current_sim_recurrent_profile_artifact_audit_route_to_checkpoint_quality_audit`
- manifest: `experiments/manifests/m2223-paper-route-current-sim-recurrent-profile-artifact-audit.json`
- parent audit: `docs/m2222-paper-route-current-sim-profile-history-failure-diagnosis-result-audit.md`
- reset in M2223: `false`
- measured execution in M2223: `false`
- policy action executed in M2223: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Scope

M2223 is an artifact/code audit only. It inspects existing profile metadata,
checkpoint materialization rows, measured-readiness rows, configs, checkpoint
metadata, and measured-runner code. It does not run reset, rollout, measured
execution, policy actions, replay, PPO, or training.

Primary artifacts inspected:

```text
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/summary.json
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json
runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/summary.json
runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/profile_checkpoint_join_rows.csv
configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
configs/paper_route_profiles/m1190_l3_reset_control_smoke.json
src/autodrift/controller_profiles.py
src/autodrift/controller_family_full_rollout_execution.py
src/autodrift/evaluate.py
```

## Findings

The L3 online and reset-control profile mapping is structurally clean:

```text
L3_online_gru:
  actor_encoder: human_view_online_gru
  env_history_length: 1
  actor_history_length: 1
  observation_dim: 72
  reset_hidden_policy: episode_persistent
  training_enabled: true
  checkpoint_materialization_mode: train_frozen_profile_config
  checkpoint_source_profile_name: L3_online_gru
  checkpoint_exists: true

L3_reset_control:
  actor_encoder: human_view_online_gru
  env_history_length: 1
  actor_history_length: 1
  observation_dim: 72
  reset_hidden_policy: every_step_control
  training_enabled: false
  checkpoint_materialization_mode: alias_same_weights_reset_hidden_control
  checkpoint_source_profile_name: L3_online_gru
  checkpoint_exists: true
```

M2171 reports `alias_profile_count=1`, `reset_control_checkpoint_source_profile=L3_online_gru`,
`reset_control_trained=false`, checkpoint paths present `320/320`, and guardrail
`0`. M2200 readiness reports `reset_control_alias_pass=true`,
`missing_checkpoint_row_count=0`, eight profiles with `288` workload rows each,
and guardrail `0`.

The measured-execution episode rows also show the intended split:

```text
L3_online_gru:
  checkpoint_path: runs/m2171.../checkpoints/L3_online_gru/checkpoint.pt
  profile_config_path: configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
  history_representation: online_recurrent_hidden
  checkpoint_materialization_mode: train_frozen_profile_config

L3_reset_control:
  checkpoint_path: runs/m2171.../checkpoints/L3_online_gru/checkpoint.pt
  profile_config_path: configs/paper_route_profiles/m1190_l3_reset_control_smoke.json
  history_representation: online_recurrent_hidden
  checkpoint_materialization_mode: alias_same_weights_reset_hidden_control
```

Static runtime routing is consistent with the intended reset semantics:

```text
controller_family_full_rollout_execution.run_workload_cell:
  loads the profile config;
  wraps the environment with that profile config;
  checks checkpoint obs_dim equals env obs_dim;
  passes runtime["reset_hidden_policy"] to ActorPolicy.

evaluate.ActorPolicy.act:
  if model is online recurrent and reset_hidden_policy == every_step_control:
    hidden is cleared before each recurrent action.
```

The L3 checkpoint metadata is also structurally consistent:

```text
obs_dim: 72
act_dim: 3
actor_encoder: human_view_online_gru
actor_history_length: 1
is_online_recurrent: true
action_sequence_horizon: 1
recurrent_sequence_training: true
total_steps: 1024
num_envs: 2
rollout_steps: 64
seed: 119006
```

## Quality Signal

The L3 checkpoint was a smoke-scale checkpoint, not a mature recurrent driver:

```text
L3_online_gru eval:
  return_mean: 39.381635195580216
  steps_mean: 64.6
  termination_rate: 0.6
  lateral_rmse_mean: 2.2316688387892
  beta_abs_error_mean: 0.19171232096809052

L3_online_gru final train row:
  step: 1024
  rollout_return_mean: 12.243239175254951
  reward_mean: 0.024563394486904144
  episode_count: 4
  episode_length_mean: 42.75
  termination_rate: 1.0
```

For context, the existing `L2_window_25` smoke checkpoint had better smoke eval
metrics:

```text
L2_window_25 eval:
  return_mean: 92.42838181199286
  termination_rate: 0.0
  lateral_rmse_mean: 0.428764030158128
```

This does not prove finite-window superiority. It only says the current L3
checkpoint is weak enough that M2221 zero-success is plausibly a
checkpoint-quality/training-lineage issue rather than an input-contract,
checkpoint-provenance, reset-control alias, or hidden-state routing mismatch.

## Remaining Artifact Gap

The old M1192 runtime-smoke artifact confirms both L3 configs instantiate and
pass basic contract/model-forward checks, but its stored rows do not include a
dedicated `reset_hidden_policy`/`reset_policy_routing_ok` field for
`L3_reset_control`. Current source code contains the expected routing, so this
is not treated as a blocker for M2223. If a future branch needs executable
evidence for reset routing, it should produce a no-rollout runtime-routing
artifact before measured rerun.

## Route Decision

M2223 routes to a checkpoint-quality/training-lineage audit, not to direct
training, repair, rerun, or ranking.

The next audit should aggregate per-profile checkpoint metadata, train metrics,
eval summaries, and M2221 failure metrics. It should answer:

```text
Is L3 zero-success explained by a weak smoke checkpoint?
Are L2 finite-window successes associated with stronger smoke checkpoint quality?
Is any profile using unfair training budget or profile-specific tuning?
Does the comparison panel need mature matched-budget checkpoint training before any ranking?
```

Still blocked:

```text
controller-family ranking;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
checkpoint/profile promotion;
new rollout or training.
```
