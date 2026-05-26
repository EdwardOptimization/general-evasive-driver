# M975 V4 Public Base Post-Promotion Exact Repair Full Public Gate Design

## Purpose

M975 designs the full public gate for the M974 selected exact-repaired
candidate.

M975 does not run PPO, promote a checkpoint, use private holdout, change actor
inputs, or claim a new public base. It only defines the gate that M976 must run.

## Candidate

Baseline public-gate base:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

M974 selected exact-repaired candidate:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Why this candidate:

- exact M297 delta versus alpha `1.0`: `-0.000044584`;
- exact M270 delta versus alpha `1.0`: `-0.000060797`;
- M267/M264 first replay: `17/17` success drops retained;
- M183/M170 first replay: `17/17` success drops retained;
- no PPO, private holdout, promotion, or actor-input change occurred in M974.

## Why A Full Gate Is Still Required

M974 only proves first replay feasibility for two surfaces. It does not prove:

- the remaining public replay surfaces still pass;
- source-diverse protected diagnostics remain acceptable;
- fresh randomized and moderate-OOD behavior do not regress;
- behavior ablation ordering is retained;
- the candidate should replace the current public-gate base.

The raw-start repair also showed a residual risk: it recovered M267/M264 only
to `16/17`, with row `15` still wrong-history-safe. So M976 must run a complete
public gate before any promotion audit.

## M976 Gate Stack

M976 should compare:

```text
baseline:  alpha_1_0
candidate: m974_base_s40
```

It can reuse the existing no-training full-gate runner:

```bash
python -m autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate
```

with explicit baseline and candidate paths. The module name is legacy, but the
gate behavior is exactly the needed one: six public replay surfaces, source
diagnostics, fresh/OOD eval, and behavior ablations without PPO or promotion.

## Proof Replay Surfaces

Required surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

Pass rule:

```text
all six public replay gates pass
M267/M264 success_drop_count remains 17 / 17
actor_inputs_changed == false
```

Source-diverse protected diagnostics and old-key diagnostics should be reported.
They are not allowed to hide a public replay failure.

## Fresh Generalization

Fresh public eval:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
seeds: 96700, 96701
episodes: 256 per seed
```

Moderate OOD eval:

```text
config: configs/eval_m574_moderate_ood_l3.json
seed: 96720
episodes: 128
```

Pass rule:

```text
candidate success_rate >= baseline success_rate - 0.01
candidate termination_rate <= baseline termination_rate + 0.01
candidate min_clearance_margin_mean >= baseline margin_mean - 0.005
candidate collision_rate <= baseline collision_rate + 0.01
```

## Behavior And Ablation

Behavior seeds:

```text
9505
9506
96730
96731
```

Candidate ablations:

```text
none
reset_recurrent_state
zero_all_response
```

Pass rule:

```text
candidate normal success >= baseline success - 0.01
candidate termination <= baseline termination + 0.01
candidate normal success >= reset success >= zero_all success
```

The behavior gate is not a self-ID proof by itself; it only prevents broad
behavior and ablation-order regressions before a promotion audit.

## Result Classes

M976 should classify into:

```text
exact_repair_full_public_gate_candidate
exact_repair_full_public_gate_contract_artifact
exact_repair_full_public_gate_proof_washout
exact_repair_full_public_gate_generalization_regression
exact_repair_full_public_gate_behavior_regression
```

The existing runner may emit legacy `direction_target_actor_fit_*` result
classes. M976's documentation and manifest should translate the route decision
into the exact-repair naming above.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate \
  --base-checkpoint runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt \
  --candidate-checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --run-dir runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate \
  --device auto \
  --fresh-episodes 256 \
  --ood-episodes 128 \
  --behavior-episodes 80
```

## Required M976 Artifacts

```text
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/summary.json
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/proof_replay_summary.csv
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/generalization_comparison.csv
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/behavior_comparison.csv
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/route_decision.csv
```

## Decision

Admit:

```text
m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation
```

M976 may only route to a separate promotion audit if proof, source diagnostics,
fresh generalization, and behavior/ablation gates all pass.
