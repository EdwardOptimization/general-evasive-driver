# M1116 V4 Public Base Failed Wrong-History Retention Actor-Update Design

## Purpose

M1116 designs the next bounded actor-update probe after M1115 exported the
failed wrong-history retention artifacts.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, mine rows, promote a checkpoint, use private holdout, or change actor
inputs.

## Parent Evidence

M1112 rejected the M1110 actor-coupling candidate as proof washout. M1113 then
showed that the failure mode was specific:

```text
lost_success_drop_events: 47
normal_lost_events: 0
wrong_history_safe_events: 47
```

M1115 materialized that diagnosis:

```text
failed_event_count: 47
target_base_failed_events: 19
family_source_failed_events: 28
target_base_rejected_trajectory_anchor_rows: 707
combined_target_base_rejected_anchor_rows: 4664
short_family_rows_in_training_anchor: false
```

The important lesson is that the M1107 exact objective can move the allowed
actor surface, but without closed-loop rejected-history retention it makes the
wrong-history branch safe. The next actor update must therefore protect the
target-base wrong-history trajectory, not only the normal branch and one-step
snippet actions.

## Design Decision

The next executable actor-update probe should combine:

```text
primary objective:
  M1107 materialized objective corpus

retention anchors:
  rollout action anchor from the current public base
  M1107 snippet action anchor including rejected hidden states
  M1115 combined target-base rejected-history trajectory anchor
```

The update is still only an actor-coupling probe:

```text
train_scope: actor_coupling
train_log_std: false
allowed changed prefixes:
  actor_mean.
  response_context_fusion.0.
forbidden changed tensors:
  log_std
  response_encoder.*
  context_encoder.*
  gru.*
  critic.*
  any actor-input contract tensor or config
```

Every candidate must restart from the current public-gate base:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

No candidate may chain from M1110 or from another candidate.

## Candidate Recipe

If the branch synthesis allows continuing, the next implementation milestone
should run exactly three small candidates:

```text
seeds: 111800, 111801, 111802
steps: 10
learning_rate: 0.000025
batch_size: 64
logprob_margin: 0.05
grad_clip_norm: 0.5
train_scope: actor_coupling
train_log_std: false
```

Use these anchors:

```text
action_anchor_coef: 100.0
snippet_action_anchor_coef: 100.0
trajectory_action_anchor_coef: 250.0
trajectory_action_anchor_snapshot_npz:
  runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz
trajectory_action_anchor_batch_size: 256
```

Primary command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --snippet-npz runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz \
  --device cpu \
  --steps 10 \
  --batch-size 64 \
  --learning-rate 0.000025 \
  --logprob-margin 0.05 \
  --seed ${SEED} \
  --train-scope actor_coupling \
  --grad-clip-norm 0.5 \
  --log-interval 2 \
  --eval-batch-size 68 \
  --eval-batches 1 \
  --eval-seed 37 \
  --action-anchor-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --action-anchor-coef 100.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed ${SEED} \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --snippet-action-anchor-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --snippet-action-anchor-coef 100.0 \
  --snippet-action-anchor-batch-size 68 \
  --trajectory-action-anchor-snapshot-npz runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz \
  --trajectory-action-anchor-coef 250.0 \
  --trajectory-action-anchor-batch-size 256 \
  --run-dir runs/m1118_failed_wrong_history_retention_actor_update_seed${SEED}
```

The lower learning rate is intentional. M1110 already showed that a small exact
objective improvement can be enough to wash out proof rows, so M1118 should
prefer a smaller step with stronger trajectory retention over a larger exact
objective movement.

## Pre-Replay Gate Order

No replay should run until these gates pass:

```text
1. M1115 target-base and combined anchors load.
2. actor-input contract is unchanged.
3. optimizer metadata confirms train_scope=actor_coupling and train_log_std=false.
4. parameter-diff audit confirms only actor_mean. and response_context_fusion.0. changed.
5. exact M1107 objective loss is no worse than base.
6. at least one candidate improves exact M1107 objective.
7. action-anchor MSE <= 0.0001.
8. snippet-action-anchor MSE <= 0.0001.
9. combined trajectory-action-anchor MSE <= 0.0001.
10. target-base-only M1115 trajectory-anchor MSE <= 0.0001.
```

The target-base-only check is separate from the combined-anchor training loss.
The combined anchor preserves earlier active-set anchors, but M1112's direct
failure was the target-base wrong-history branch becoming safe. That specific
family must not be hidden by aggregate anchor metrics.

## Replay Gate Order

If a candidate passes the pre-replay gates, the next gate design may admit replay
in this order:

```text
1. old public first replay:
   m183_m168
   m223_m219
   m267_m264

2. source-diverse first replay:
   current_m333_surface
   m314_continuity_surface
   m317_continuity_surface

3. family-intersection replay:
   short61049
   short61050
   short61051

4. full expanded public proof replay stack.

5. fresh/OOD and behavior seeds.
```

The family-intersection rows remain mandatory gates, but not training anchors.
If they fail while target-base rows pass, the route should be family-source
target-policy materialization rather than direct short-family hidden-state
anchoring.

## Positive Candidate Criteria

A candidate may be forwarded to first-replay gate design only if all are true:

```text
exact M1107 objective loss <= base exact loss;
loss_mean_improvement > 0.0 in optimizer summary;
after_action_anchor_mse <= 0.0001;
after_snippet_action_anchor_mse <= 0.0001;
after_trajectory_action_anchor_mse <= 0.0001;
target_base_only_trajectory_anchor_mse <= 0.0001;
changed parameter names are all in allowed prefixes;
log_std is unchanged;
actor inputs are unchanged;
PPO was not used;
private holdout was not used;
promotion did not occur.
```

If no seed passes, the correct next step is a conflict audit, not more seeds or
a larger learning rate.

## Result Classes For The Next Probe

Use these classifications:

```text
failed_wrong_history_retention_actor_update_exact_candidate:
  at least one candidate passes exact, anchor, and parameter-scope gates.

failed_wrong_history_retention_actor_update_no_exact_candidate:
  all candidates run but none improve exact M1107 without violating retention.

failed_wrong_history_retention_actor_update_trajectory_anchor_regression:
  exact objective improves but M1115 trajectory retention drifts beyond threshold.

failed_wrong_history_retention_actor_update_contract_artifact:
  a candidate changes forbidden parameters or actor-input contract metadata.

failed_wrong_history_retention_actor_update_training_failure:
  optimizer command fails or produces invalid artifacts.
```

## Branch-Cadence Constraint

The `materialized_objective_corpus_sanity` branch reaches the 10-milestone
synthesis cadence after M1116. Therefore the next milestone should be a process
synthesis before running the actor-update probe. That synthesis should decide
whether to open a new `failed_wrong_history_retention_repair` branch for the
M1118 implementation.

## Explicit Non-Goals

M1116 and the next synthesis must not:

- run actor training;
- run PPO;
- run replay;
- use short-family hidden states as training anchors;
- use private holdout;
- promote a checkpoint;
- change actor inputs;
- claim scenario-distribution improvement;
- claim level3 anticipatory self-identification.

## Decision

```text
failed_wrong_history_retention_actor_update_design_route_to_branch_synthesis
```

Next milestone:

```text
m1117-v4-public-base-materialized-objective-branch-synthesis
```
