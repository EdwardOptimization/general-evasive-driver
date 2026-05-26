# M973 V4 Public Base Post-Promotion PPO Exact Repair Projection Design

## Purpose

M973 designs the response to the M972 smoke-PPO result.

M972 is not a failed training run. It is a useful diagnostic: PPO can move from
the promoted alpha `1.0` public-gate base without broad behavior regression,
but the raw PPO checkpoint is not proof-retaining.

M973 therefore treats PPO as a proposal generator and restores proof feasibility
through exact full-corpus repair/projection before any replay promotion.

M973 does not train PPO, promote a checkpoint, use private holdout, change
actor inputs, or claim new driver capability.

## M972 Failure Shape

Base checkpoint:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Raw PPO proposal:

```text
runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt
```

M972 result:

```text
result_class: post_promotion_guarded_ppo_proof_washout
proof_replay_gates_passed: 5 / 6
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
```

The only failed surface is M267/M264:

```text
base success-drop count: 17 / 17
raw PPO success-drop count: 15 / 17
```

The failing rows are `6` and `15`. In both rows, normal-history success remains
true and normal margin improves, but wrong-history margin crosses from slightly
negative to slightly positive. This means the PPO step washes out the
counterfactual wrong-history proof while keeping aggregate behavior intact.

## Repair Problem

Define:

```text
theta_base = M964 alpha_1_0 public-gate base
theta_raw  = M972 raw PPO checkpoint
theta_proj = repaired candidate
```

The repair objective is lexicographic:

1. Preserve the P0 human-view actor-input contract.
2. Restore exact proof-objective no-regression versus `theta_base`.
3. Restore first closed-loop proof gates.
4. Only then consider whether any PPO proposal movement is retained.

In optimization terms:

```text
find theta_proj near theta_base and/or theta_raw

subject to:
  exact_M297(theta_proj) <= exact_M297(theta_base) + tol
  exact_M270(theta_proj) <= exact_M270(theta_base) + tol
  actor_inputs_changed == false

then minimize:
  distance_to_theta_raw where feasible
  plus action/trajectory anchors against theta_base proof surfaces
```

This is not a scalar PPO auxiliary coefficient change. Exact full-corpus
residuals are first-class feasibility constraints.

## Existing Tooling

The existing tool is:

```bash
python -m autodrift.exact_post_ppo_repair
```

It already supports:

```text
start modes: repair_from_raw, repair_from_base, line_search_boundary
exact M297 rejected-history preference loss
exact M270 outcome-intervention loss
trajectory action anchors
parameter trust region to base
optional raw-proposal pull
best-feasible candidate selection
```

M973 should reuse this tool before adding new code. If the tool cannot express
the M972 failure, the next step is objective-coverage audit, not PPO.

## Candidate Family

M974 should generate at least three repair candidates:

| Candidate | Start mode | Purpose |
| --- | --- | --- |
| raw_s40 | `repair_from_raw` | test whether M972 PPO movement is recoverable |
| base_s40 | `repair_from_base` | test whether exact repair just returns to a base-near direction |
| line_boundary_s40 | `line_search_boundary` | find the nearest base-to-raw boundary before repair |

All candidates should use the same base, raw checkpoint, exact corpora, and
trainable-surface contract.

## Exact Corpora

Required exact corpora:

```text
M297 rejected-history preference:
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz

M270 source-balanced outcome intervention:
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

Required trajectory anchor:

```text
runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
```

Optional if first repair cannot restore M267/M264:

```text
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
runs/m389_m267_row15_conflict_corpus/current_family_conflict_corpus.npz
```

These optional corpora should be introduced only in a follow-up milestone if
M974 shows that M297/M270 plus M293 do not cover the M972 failing rows.

## Candidate Generation Defaults

M974 should start conservative:

```text
steps: 40
learning_rate: 5e-6
train_scope: actor_coupling
train_log_std: false
selection_policy: best_feasible
exact_m297_tolerance: 1e-7
exact_m270_tolerance: 1e-7
lambda_m297: 1000000
lambda_m270: 1000000
lambda_action_anchor: 100
lambda_replay_trajectory_anchor: 1
lambda_param_base: 1
lambda_param_raw: 0.05 for raw-start only
```

Line-search alphas:

```text
0,0.001,0.0025,0.005,0.01,0.025,0.05,0.1
```

The raw-start candidate may use a small raw pull. Base-start and boundary-start
candidates should prioritize feasibility and base trust region.

## Acceptance Order

M974 must use this order:

1. Candidate checkpoint exists and actor-input contract is unchanged.
2. Exact M297 no-regression versus alpha `1.0`.
3. Exact M270 no-regression versus alpha `1.0`.
4. Select the best exact-passing candidate by exact improvement and retained raw
   movement.
5. Run M267/M264 first replay gate.
6. Run M183/M170 first replay gate.
7. If both first replay gates pass, route to a separate full public-gate
   milestone.

If no exact candidate passes, classify as `objective_overfit` or
`proof_washout` depending on whether the raw proposal cannot be repaired or the
exact residuals fail to cover replay behavior.

If exact gates pass but M267/M264 replay still fails, classify as
`metric_artifact` or `objective_overfit` and design an objective coverage audit.

## Explicit Non-Goals

M973 and M974 must not:

- run longer PPO;
- increase PPO scalar auxiliary coefficients as the main fix;
- use private holdout;
- promote M972 raw or repaired candidates without a later full gate;
- change actor input/output contract;
- relax M267/M264 success-drop retention.

## Proposed M974 Commands

Raw-start candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt \
  --raw-checkpoint runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --replay-trajectory-anchor-npz runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz \
  --start-mode repair_from_raw \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-replay-trajectory-anchor 1 \
  --lambda-param-raw 0.05 \
  --device auto \
  --seed 5973 \
  --run-dir runs/m974_exact_repair_from_raw_s40_seed5973
```

Base-start and line-boundary candidates should use the same arguments except
`--start-mode`, `--seed`, `--run-dir`, and `--lambda-param-raw 0.0`.

## Next Blocker

```text
m974-v4-public-base-post-promotion-exact-repair-projection-probe
```

M974 should implement this no-PPO repair/projection probe and run only first
proof gates after exact no-regression passes.
