# M1028 V4 Public Base Candidate B Post-PPO Exact Repair Design

## Purpose

M1028 designs the repair route after M1026/M1027 showed that a smoke-scale PPO
proposal from Candidate B is trainable and broadly behavior-retaining, but not
proof-retaining.

M1028 is design only. It does not run repair, PPO, training, private holdout,
promotion, or actor-input changes.

## Parent State

Current public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

M1026 raw PPO proposal:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

M1027 localized the blocker:

```text
surface: M267/M264
row_id: 15
physical_pair_key: 9530:21:9550:21
target: future_braking_deceleration
baseline wrong-history margin: -0.000112
raw PPO wrong-history margin: +0.000311
normal_margin_delta: +0.000533
wrong_history_margin_delta: +0.000423
```

The M1026 raw checkpoint is useful as a proposal but not acceptable as a base.
It passes exact temporal retention, fresh public/OOD, and behavior/ablation
checks while failing one current-family wrong-history proof row.

## Repair Framing

Define:

```text
theta_base = Candidate B public-gate base
theta_raw  = M1026 raw PPO proposal
theta_proj = repaired candidate
```

M1029 should treat PPO as a proposal generator and exact repair/projection as
the feasibility-restoration step:

```text
find theta_proj near theta_raw when feasible

subject to lexicographic constraints:
  1. P0 actor-input contract unchanged
  2. M297/M270 exact no-regression versus theta_base
  3. M997 temporal exact retention versus theta_base
  4. M267/M264 row 15 wrong-history remains a failure
  5. M267/M264 full surface retains 17/17 success drops
  6. M183/M170 first replay retains 17/17 success drops
  7. broad public proof/generalization/behavior gates are left to a later full gate
```

No scalar aggregate objective may override proof replay. If exact objectives
improve but row 15 becomes safe, the candidate is rejected.

## Existing Tooling

Use the existing exact repair tool:

```bash
python -m autodrift.exact_post_ppo_repair
```

It already supports:

```text
start modes:
  repair_from_raw
  repair_from_base
  line_search_boundary

exact objectives:
  M297 rejected-history preference
  M270 outcome intervention

anchors and constraints:
  replay trajectory anchor
  current-family conflict corpus
  parameter trust region to base
  optional raw-proposal pull
  best-feasible candidate selection
```

M1029 should reuse this tool before adding a new optimizer. If the tool cannot
express the M1026 failure, the next step is an objective-coverage audit, not
longer PPO.

## Required Corpora

Exact M297 preference:

```text
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
```

Exact M270 outcome intervention:

```text
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

Rejected-history trajectory anchor:

```text
runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
```

Current-family conflict residual for row15/row6:

```text
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
```

The older row15 conflict corpus remains diagnostic:

```text
runs/m389_m267_row15_conflict_corpus/current_family_conflict_corpus.npz
```

M1029 should use the M393 corpus first because it exports collision-side
rejected-history targets and was created specifically after row15 remained a
knife-edge boundary.

## Candidate Family

M1029 should generate exactly three no-PPO repair candidates:

| Candidate | Start mode | Purpose |
| --- | --- | --- |
| raw_conflict_s40 | `repair_from_raw` | test whether useful M1026 PPO movement is recoverable |
| base_conflict_s40 | `repair_from_base` | test whether the repair must return to a base-near direction |
| line_conflict_s40 | `line_search_boundary` | find the nearest base-to-raw feasible boundary before repair |

All candidates use the same base/raw checkpoints, exact corpora, M393 conflict
corpus, and replay trajectory anchor.

## Candidate Generation Defaults

Start conservative:

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
lambda_current_family_conflict: 1000
lambda_current_family_conflict_rejected: 10
lambda_replay_trajectory_anchor: 1
lambda_action_anchor: 100
lambda_param_base: 1
lambda_param_raw: 0.05 for raw-start only, otherwise 0
```

Line-search alphas:

```text
0,0.001,0.0025,0.005,0.01,0.025,0.05,0.1
```

Rationale:

```text
M1026 row15 failure is a rejected-branch lift, so the M393 conflict residual
must be stronger than ordinary replay trajectory anchoring but still subordinate
to exact feasibility and replay gates.
```

## Proposed M1029 Commands

Raw-start candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --raw-checkpoint runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --current-family-conflict-npz runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz \
  --replay-trajectory-anchor-npz runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz \
  --start-mode repair_from_raw \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-current-family-conflict 1000 \
  --lambda-current-family-conflict-rejected 10 \
  --lambda-replay-trajectory-anchor 1 \
  --lambda-param-raw 0.05 \
  --device auto \
  --seed 61028 \
  --run-dir runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028
```

Base-start candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --raw-checkpoint runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --current-family-conflict-npz runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz \
  --replay-trajectory-anchor-npz runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz \
  --start-mode repair_from_base \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-current-family-conflict 1000 \
  --lambda-current-family-conflict-rejected 10 \
  --lambda-replay-trajectory-anchor 1 \
  --lambda-param-raw 0.0 \
  --device auto \
  --seed 61029 \
  --run-dir runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029
```

Line-boundary candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --raw-checkpoint runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --current-family-conflict-npz runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz \
  --replay-trajectory-anchor-npz runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz \
  --start-mode line_search_boundary \
  --line-search-alphas 0,0.001,0.0025,0.005,0.01,0.025,0.05,0.1 \
  --steps 40 \
  --learning-rate 5e-6 \
  --lambda-current-family-conflict 1000 \
  --lambda-current-family-conflict-rejected 10 \
  --lambda-replay-trajectory-anchor 1 \
  --lambda-param-raw 0.0 \
  --device auto \
  --seed 61030 \
  --run-dir runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030
```

## Gate Order For M1029

M1029 must use this order:

1. Candidate checkpoint exists.
2. P0 actor-input contract unchanged.
3. Exact M297 no-regression versus Candidate B.
4. Exact M270 no-regression versus Candidate B.
5. M997 temporal exact retention versus Candidate B.
6. M267/M264 first replay passes `17/17`, with row15 wrong-history collision
   retained.
7. M183/M170 first replay passes `17/17`.
8. If both first replay gates pass, route to a separate full public gate.

M1029 should not run full public gates for exact-regressing candidates. M1029
should not promote any candidate.

## Required M1029 Artifacts

Candidate repair artifacts:

```text
runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028/summary.json
runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/summary.json
runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030/summary.json
```

First replay artifacts:

```text
runs/m1029_candidate_b_repair_m267_m264_first_replay/summary.json
runs/m1029_candidate_b_repair_m183_m170_first_replay/summary.json
```

Temporal exact retention artifact:

```text
runs/m1029_candidate_b_repair_temporal_exact_retention/summary.json
```

## Result Classification

Use these route classes:

```text
candidate_b_post_ppo_exact_repair_first_replay_candidate:
  exact M297/M270 pass, M997 temporal exact passes, M267/M264 and M183/M170
  first replay pass. Route to full public gate design.

candidate_b_post_ppo_exact_repair_no_exact_candidate:
  no candidate passes exact M297/M270. Route to exact objective conflict audit.

candidate_b_post_ppo_exact_repair_temporal_regression:
  M297/M270 pass but M997 temporal exact regresses. Route to temporal-objective
  repair integration design.

candidate_b_post_ppo_exact_repair_proof_washout:
  exact objectives pass but M267/M264 or M183/M170 first replay fails. Route to
  row-specific objective coverage audit.

candidate_b_post_ppo_exact_repair_base_equivalent:
  proof-safe candidate exists but retains no useful movement relative to base.
  Route to PPO recipe audit instead of full public gate.
```

## Non-Goals

M1028/M1029 must not:

- run longer PPO;
- increase PPO scalar auxiliary coefficients as the main fix;
- use private holdout;
- promote M1026 raw or repaired candidates;
- change actor input/output contract;
- relax M267/M264 success-drop retention;
- accept aggregate generalization when row15 proof fails.

## Decision

```text
candidate_b_post_ppo_exact_repair_design_admit_m1029_probe
```

Next milestone:

```text
m1029-v4-public-base-candidate-b-post-ppo-exact-repair-probe
```
