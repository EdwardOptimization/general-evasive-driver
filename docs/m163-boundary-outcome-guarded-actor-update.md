# M163 Boundary-Outcome Guarded Actor Update

M162 admitted the M156 boundary-outcome corpus for guarded actor-update design,
not PPO. M163 tests whether that corpus can produce a low-drift actor-coupling
update that improves the fixed outcome objective while preserving behavior and
the protected critical key.

This milestone still does not prove driver-level self-identification. It tests
whether the M162 training signal can be safely attached to the actor.

## Setup

Initial checkpoint:

```text
runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt
```

M162 corpus:

```text
runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
```

The actor update uses:

```text
train_scope = actor_coupling
trainable = response_context_fusion + actor_mean
frozen = response encoder, context encoder, GRU, critic, log_std
```

The deployed actor input contract is unchanged. M162 labels, target ids, group
ids, geometry keys, and outcome scores remain training-time artifacts only.

## Rejected 80-Step Candidate

Run:

```text
runs/m163_boundary_outcome_actor_coupling_anchor100_seed9831
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --snippet-npz runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz \
  --device cpu \
  --steps 80 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 9831 \
  --grad-clip-norm 1.0 \
  --log-interval 20 \
  --eval-batch-size 64 \
  --eval-batches 30 \
  --eval-seed 0 \
  --train-scope actor_coupling \
  --action-anchor-checkpoint runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --action-anchor-coef 100.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed 9831 \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --run-dir runs/m163_boundary_outcome_actor_coupling_anchor100_seed9831
```

Objective:

| Metric | Value |
| --- | ---: |
| before loss mean | 0.404754 |
| after loss mean | 0.392899 |
| loss improvement | 0.011856 |
| after action-anchor MSE | 0.000052 |

The 80-step candidate preserved the cheap behavior gates, but failed the
protected critical key:

```text
runs/m163_critical_key_anchor100_seed9944
m163_a100 accepted_cases=0/1
policy_pass=false
```

Decision: reject the 80-step candidate.

## Accepted 20-Step Candidate

Run:

```text
runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --snippet-npz runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz \
  --device cpu \
  --steps 20 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 9832 \
  --grad-clip-norm 1.0 \
  --log-interval 5 \
  --eval-batch-size 64 \
  --eval-batches 30 \
  --eval-seed 0 \
  --train-scope actor_coupling \
  --action-anchor-checkpoint runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --action-anchor-coef 100.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed 9832 \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --run-dir runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832
```

Objective:

| Metric | Value |
| --- | ---: |
| before loss mean | 0.404754 |
| after loss mean | 0.400771 |
| loss improvement | 0.003984 |
| after action-anchor MSE | 0.000019 |
| objective pass | true |

Independent fixed-batch outcome evaluation:

```text
runs/m163_fixed_batch_outcome_eval_anchor100_s20_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m156_s20 | 0.402310 |
| m163_a100_s20 | 0.398315 |

## Behavior Retention

Both gates use `configs/m121_human_view_zero_obstacle_relvel.json`, 80
episodes, and compare M142, M156, M163, and M163 response-history ablations.

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m142_a400 | 0.8625 | 0.1375 | 1.841495 |
| m156_s20 | 0.8625 | 0.1375 | 1.845927 |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.846266 |
| m163_a100_s20_reset | 0.8500 | 0.1250 | 1.842207 |
| m163_a100_s20_zero_current | 0.8000 | 0.1250 | 1.856585 |
| m163_a100_s20_zero_all | 0.8000 | 0.1250 | 1.856585 |
| m163_a100_s20_noact | 0.8625 | 0.1375 | 1.848115 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m142_a400 | 0.8625 | 0.1375 | 1.849323 |
| m156_s20 | 0.8625 | 0.1375 | 1.853662 |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.853828 |
| m163_a100_s20_reset | 0.8500 | 0.1250 | 1.850347 |
| m163_a100_s20_zero_current | 0.8000 | 0.1250 | 1.868565 |
| m163_a100_s20_zero_all | 0.8000 | 0.1250 | 1.868565 |
| m163_a100_s20_noact | 0.8625 | 0.1375 | 1.857104 |

Behavior retention passes on both seeds. The response ablations still degrade
success; no-action history remains behavior-neutral.

## Protected Critical Key

Run:

```text
runs/m163_critical_key_anchor100_s20_seed9944
```

Result:

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m142_a400 | 1 / 1 | true |
| m156_s20 | 1 / 1 | true |
| m163_a100_s20 | 1 / 1 | true |

`guard_validated=false` only because no non-reference policy failed in this
run. The relevant evidence is `m163_a100_s20 policy_pass=True`.

## Decision

M163 is a guarded actor-update positive for the 20-step anchor100 candidate:

```text
runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt
```

What passed:

- fixed M162 outcome objective improves;
- independent fixed-batch outcome eval improves versus M156;
- action-anchor MSE stays very small;
- behavior success matches M142/M156 on seeds 9503 and 9504;
- reset and zero-response ablations still reduce success;
- protected critical key passes.

What remains weak:

- the objective improvement is small;
- this is one accepted optimizer seed after the 80-step variant failed the
  protected key;
- the result does not yet prove actual boundary rollout outcome improvement;
- no-action-history remains neutral;
- no PPO continuation has been run.

Decision: admit the 20-step M163 checkpoint for an actual boundary-outcome
replay gate and guarded PPO-smoke design. Do not run large PPO or claim
driver-like self-identification from M163 alone.

## Validation

```text
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9503
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9504
PYTHONPATH=src python -m autodrift.critical_key_replay_guard ...
```
