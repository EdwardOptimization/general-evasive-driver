# M976 V4 Public Base Post-Promotion Exact Repair Full Public Gate Implementation

## Purpose

M976 runs the no-training full public gate designed in M975 for the M974
selected exact-repaired candidate.

M976 does not train, run PPO, promote, use private holdout, or change actor
inputs.

## Candidate

Baseline:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Candidate:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

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

## Result

The underlying runner emits the legacy result class:

```text
direction_target_actor_fit_promotion_gate_candidate
```

For this branch, the corresponding result is:

```text
exact_repair_full_public_gate_candidate
```

Summary:

```text
proof_pass: true
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
ppo_used: false
promoted: false
private_holdout_used: false
source_diverse_protected_status: pass
old_key_9944_status: diagnostic_only
```

## Proof Replay

All six public replay surfaces pass.

| Surface | Rows | Base success-drop | Candidate success-drop | Normal margin delta | Margin-gap delta | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 | 16 | +0.000033193 | +0.000030558 | pass |
| M183/M170 | 17 | 17 | 17 | +0.000033003 | +0.000030074 | pass |
| M193/M189 | 14 | 14 | 14 | +0.000029649 | +0.000025826 | pass |
| M212/M204 | 17 | 17 | 17 | +0.000030670 | +0.000025117 | pass |
| M223/M219 | 17 | 17 | 17 | +0.000030677 | +0.000025125 | pass |
| M267/M264 | 17 | 17 | 17 | +0.000030687 | +0.000025134 | pass |

Source-diverse protected diagnostic:

```text
replay_gates_passed: 3 / 3
overall_pass: true
```

Old-key neighborhood remains diagnostic-only. Both baseline and candidate have
`policy_pass=false`, but the candidate has slightly more accepted cases
(`38/40` versus `37/40`). This diagnostic does not veto because it was not a
promotion-blocking gate for this branch.

## Fresh Generalization

| Distribution | Seed | Base success | Candidate success | Margin delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| fresh_public | 96700 | 0.83984375 | 0.83984375 | +0.000137246 | true |
| fresh_public | 96701 | 0.83984375 | 0.83984375 | +0.000136760 | true |
| moderate_ood | 96720 | 0.625 | 0.625 | +0.000051507 | true |

No success, termination, or collision regression is observed under the public
fresh/OOD gate.

## Behavior And Ablation

| Seed | Base success | Candidate success | Reset success | Zero-all success | Pass |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9505 | 0.8625 | 0.8625 | 0.85 | 0.8 | true |
| 9506 | 0.8625 | 0.8625 | 0.85 | 0.8 | true |
| 96730 | 0.8375 | 0.8375 | 0.825 | 0.825 | true |
| 96731 | 0.8375 | 0.8375 | 0.825 | 0.825 | true |

Reset/zero-all ordering is retained for all behavior seeds.

## Decision

M976 passes the full public gate and routes to a separate promotion audit.

Decision:

```text
exact_repair_full_public_gate_candidate_route_to_promotion_audit
```

Next:

```text
m977-v4-public-base-post-promotion-exact-repair-promotion-audit
```

## Artifacts

```text
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/summary.json
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/proof_replay_summary.csv
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/generalization_comparison.csv
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/behavior_comparison.csv
runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/route_decision.csv
```
