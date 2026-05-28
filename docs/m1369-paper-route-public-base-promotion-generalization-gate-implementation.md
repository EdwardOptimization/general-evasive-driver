# M1369 Paper-Route Public-Base Promotion Generalization Gate Implementation

## Summary

M1369 implements and runs the no-training public-base
promotion/generalization gate designed in M1368.

Result:

```text
materialized_source_history_public_base_promotion_gate_candidate
```

Candidate:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Current public base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Artifact:

```text
runs/m1369_public_base_promotion_generalization_gate/summary.json
```

M1369 does not promote the checkpoint. It only classifies M1362 alpha `0.1` as a
promotion-audit candidate. Actual public-base replacement must be a separate
M1370 audit.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_public_base_promotion_generalization_gate \
  --base-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --candidate-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --corpus-run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --run-dir runs/m1369_public_base_promotion_generalization_gate \
  --device auto \
  --fresh-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --ood-env-config configs/eval_m574_moderate_ood_l3.json \
  --fresh-seeds 136900,136901,136902 \
  --ood-seeds 136920,136921 \
  --behavior-seeds 9505,9506,136930,136931 \
  --fresh-episodes 256 \
  --ood-episodes 128 \
  --behavior-episodes 80 \
  --max-continuation-steps 60
```

## Tier Results

```text
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
training_started: false
ppo_used: false
private_holdout_used: false
promoted: false
```

## Exact Source-History Retention

The exact tier recomputed the M1336 materialized source-history corpus and
M1342 pair-group metric interpretation.

```text
combined_loss_delta_vs_base: -0.5148637358
group_min_joint_margin_delta_vs_base: +0.5245143158
eval_fold_4_group_min_joint_margin_delta_vs_base: +0.4884667325
allowed_parameter_l2: 0.1266231245
allowed_parameter_max_abs: 0.0009239744
actor_inputs_changed: false
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
```

Interpretation:

```text
The candidate preserves the actor input contract and improves the exact
source-history objective relative to M1154 under the same corpus and metric
schema.
```

## Public Proof Replay

All six public replay surfaces passed.

| surface | rows | base drops | candidate drops | normal margin delta | gap delta | gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 | 16 | -0.000948 | -0.000249 | pass |
| M183/M170 | 17 | 17 | 17 | -0.000932 | -0.000248 | pass |
| M193/M189 | 14 | 14 | 14 | -0.000685 | -0.000237 | pass |
| M212/M204 | 17 | 17 | 17 | -0.000690 | -0.000194 | pass |
| M223/M219 | 17 | 17 | 17 | -0.000690 | -0.000194 | pass |
| M267/M264 | 17 | 17 | 17 | -0.000689 | -0.000194 | pass |

Source-diverse protected diagnostics also passed:

```text
replay_gates_passed: 3
replay_gates_failed: 0
overall_pass: true
```

The old `9944|perturbed|28|28` key remains diagnostic-only:

```text
candidate accepted cases: 25 / 40
public base accepted cases: 24 / 40
single-key policy pass: false for both
```

This does not veto the candidate because the source-diverse protected diagnostic
passed and M1368 explicitly demoted the old singleton to diagnostic-only.

## Fresh Public And Moderate-OOD Generalization

All fresh/OOD comparisons passed.

| distribution | seed | base success | candidate success | success delta | margin delta | collision delta | gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| fresh_public | 136900 | 0.875000 | 0.875000 | 0.000000 | +0.000839 | 0.000000 | pass |
| fresh_public | 136901 | 0.875000 | 0.875000 | 0.000000 | +0.000839 | 0.000000 | pass |
| fresh_public | 136902 | 0.875000 | 0.875000 | 0.000000 | +0.000851 | 0.000000 | pass |
| moderate_ood | 136920 | 0.640625 | 0.640625 | 0.000000 | +0.001779 | 0.000000 | pass |
| moderate_ood | 136921 | 0.648438 | 0.648438 | 0.000000 | +0.001760 | 0.000000 | pass |

Interpretation:

```text
M1362 alpha 0.1 does not regress M1154 on this public fresh/OOD evaluation and
slightly improves mean clearance margin on every compared row.
```

This is still public generalization evidence, not private holdout or paper-level
source-rich extreme validation.

## Behavior And Ablation Retention

All behavior seeds passed, including two new public behavior seeds.

| seed | base success | candidate success | reset success | zero-all success | gate |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9505 | 0.862500 | 0.862500 | 0.850000 | 0.800000 | pass |
| 9506 | 0.862500 | 0.862500 | 0.850000 | 0.800000 | pass |
| 136930 | 0.875000 | 0.875000 | 0.862500 | 0.837500 | pass |
| 136931 | 0.875000 | 0.875000 | 0.862500 | 0.837500 | pass |

The normal >= reset >= zero-all ordering is retained.

This is a behavior-retention diagnostic. It is not enough to claim level3
anticipatory self-identification.

## Decision

M1369 passes as a promotion/generalization gate:

```text
public-base promotion audit candidate: true
next: m1370-paper-route-public-base-promotion-audit
```

The separate promotion audit must decide whether the official public base should
move from M1154 to M1362 alpha `0.1`. That audit should also restate the claim
boundary:

```text
allowed:
  public-base promotion candidate / possible public-base replacement

not allowed:
  private-holdout claim
  source-rich extreme paper claim
  level3 recurrent-belief/self-identification claim
  PPO continuation stability claim
  high-fidelity or real-vehicle claim
```

## Guardrails

M1369 performs no training, PPO, actor update, checkpoint mutation, promotion,
private holdout, threshold relaxation, actor-input expansion, high-fidelity
claim, paper-level claim, or level3 self-identification claim.

## Next

```text
m1370-paper-route-public-base-promotion-audit
```
