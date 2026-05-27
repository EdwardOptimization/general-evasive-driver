# M1146 V4 Public Base Row15 Promoted Guarded Actor Update Design

## Purpose

M1146 designs the first actor-update probe admitted by M1145.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, build a corpus, run objective sanity, mine rows, promote a checkpoint,
use private holdout, or change actor inputs.

## Parent Evidence

M1144 produced a valid row15-current materialized objective corpus:

```text
snippet npz:
  runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz

corpus_rows: 76
physical_pairs: 13
targets: 2
success_drop_rows: 76
action_reconstruction_error_max: 0.0
objective_pass: true
seed_pass_count: 3
min_val_combined_loss_improvement: 2.906849
min_val_delta_loss_improvement: 3.633356
mean_val_pairwise_accuracy_after: 1.0
```

M1145 audited that result and admitted only a guarded actor-update design. It
explicitly did not admit direct actor update, PPO, promotion, private holdout,
or driver-improvement claims.

## Guarded Update Contract

The next implementation milestone may run a bounded action-grounding posttrain
probe from the current public-gate base:

```text
base checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

snippet npz:
  runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz

env config:
  configs/m121_human_view_zero_obstacle_relvel.json
```

Allowed update surface:

```text
train_scope: actor_coupling
allowed changed prefixes:
  actor_mean.
  response_context_fusion.0.
forbidden changed tensors:
  log_std
  response_encoder.*
  context_encoder.*
  gru.*
  critic.*
  any actor-input contract tensor or config change
```

The update must not chain from another M1147 candidate. Every seed restarts from
the same alpha `0.15` public-gate base.

## M1147 Candidate Recipe

M1147 should run three independent low-drift candidates:

```text
seeds: 114600, 114601, 114602
steps: 10
learning_rate: 0.00005
batch_size: 64
logprob_margin: 0.05
grad_clip_norm: 0.5
train_scope: actor_coupling
train_log_std: false
```

Use both retention anchors:

```text
action_anchor_coef: 100.0
action_anchor_checkpoint: base checkpoint
action_anchor_env_config: configs/m121_human_view_zero_obstacle_relvel.json
action_anchor_episodes: 30
action_anchor_horizon_steps: 15
action_anchor_sample_stride: 3
action_anchor_max_samples: 800

snippet_action_anchor_coef: 100.0
snippet_action_anchor_checkpoint: base checkpoint
snippet_action_anchor_preferred_only: false
```

The snippet anchor intentionally includes rejected hidden states. The earlier
M279-M286 lesson remains active: repairing the normal branch while allowing the
wrong-history branch to become safe destroys the self-ID proof surface.

Primary command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --snippet-npz runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz \
  --device cpu \
  --steps 10 \
  --batch-size 64 \
  --learning-rate 0.00005 \
  --logprob-margin 0.05 \
  --seed ${SEED} \
  --train-scope actor_coupling \
  --grad-clip-norm 0.5 \
  --log-interval 2 \
  --eval-batch-size 76 \
  --eval-batches 1 \
  --eval-seed 37 \
  --action-anchor-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --action-anchor-coef 100.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed ${SEED} \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --snippet-action-anchor-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --snippet-action-anchor-coef 100.0 \
  --snippet-action-anchor-batch-size 76 \
  --run-dir runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed${SEED}
```

## Gate Order

M1147 must evaluate candidates in this order:

```text
1. actor-input contract unchanged;
2. optimizer metadata confirms train_scope=actor_coupling and train_log_std=false;
3. parameter-diff audit confirms only actor_mean. and response_context_fusion.0. changed;
4. exact M1144 objective no-regression versus base;
5. exact M1144 objective improvement for at least one candidate;
6. action-anchor and snippet-action-anchor MSE remain low;
7. no replay is run until steps 1-6 pass;
8. no PPO, promotion, private holdout, mining, or corpus rebuild occurs.
```

If no candidate passes steps 1-6, M1147 should complete as a negative result
and route to a recipe audit rather than replay.

If at least one candidate passes steps 1-6, the next milestone may design first
replay gates. Replay is still not promotion. It must include:

```text
old public replay surfaces;
M1061 family-intersection public gate;
row15 promoted-base family/intersection surfaces;
M1139/M1142 materialized row sanity;
source-diverse diagnostics;
behavior seeds 9505 and 9506 at minimum.
```

## Positive Candidate Criteria

A candidate may be forwarded to replay design only if all are true:

```text
exact M1144 objective loss <= base exact loss;
loss_mean_improvement > 0.0 in optimizer summary;
after_action_anchor_mse <= 0.0001;
after_snippet_action_anchor_mse <= 0.0001;
changed parameter names are all in allowed prefixes;
log_std is unchanged;
actor inputs are unchanged;
PPO was not used;
private holdout was not used;
promotion did not occur.
```

These thresholds are deliberately small-step. The goal is not to create a new
driver claim. The goal is to test whether the materialized objective can move
the allowed action surface without immediately violating proof discipline.

## Result Classes For M1147

Use these classifications:

```text
row15_promoted_guarded_actor_update_exact_candidate:
  at least one candidate passes objective, anchor, and parameter-scope gates.

row15_promoted_guarded_actor_update_no_exact_candidate:
  all candidates run but none improve exact objective without violating anchors.

row15_promoted_guarded_actor_update_contract_artifact:
  a candidate changes forbidden parameters or actor-input contract metadata.

row15_promoted_guarded_actor_update_anchor_regression:
  exact objective improves but action or snippet anchors drift beyond threshold.

row15_promoted_guarded_actor_update_training_failure:
  optimizer command fails or produces invalid artifacts.
```

## Explicit Non-Goals

M1146 and M1147 must not:

- run PPO;
- run replay before exact and contract gates;
- use private holdout;
- promote a checkpoint;
- change actor inputs;
- claim scenario-distribution improvement;
- claim level3 anticipatory self-identification.

## Decision

```text
row15_promoted_guarded_actor_update_design_admit_probe
```

Next milestone:

```text
m1147-v4-public-base-row15-promoted-guarded-actor-update-probe
```
