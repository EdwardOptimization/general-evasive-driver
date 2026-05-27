# M1112 V4 Public Base Materialized Actor Update Full Public Gate

## Purpose

M1112 evaluates the M1110 primary materialized actor-update candidate under the
pre-registered M1111 gate.

It runs an exact M1107 recheck and the expanded full public gate. It does not
train actor weights, run PPO, promote, use private holdout, change actor inputs,
or switch candidates.

## Candidate

Base checkpoint:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Candidate:

```text
runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt
```

## Exact M1107 Recheck

Artifact:

```text
runs/m1112_materialized_actor_update_m1107_exact_eval/summary.json
```

| Policy | Exact M1107 loss |
| --- | ---: |
| `proof_current` | 0.679117 |
| `m1110_110901` | 0.674349 |

The materialized objective remains improved. The M1107 exact gate is not the
failure.

## Expanded Full Public Gate

Artifact:

```text
runs/m1112_materialized_actor_update_full_public_gate/summary.json
```

Result:

```text
result_class: candidate_b_combined_active_set_full_public_gate_public_replay_washout
exact_pass: true
actor_inputs_changed: false
allowed_surface_contract_pass: true
proof_pass: false
family_intersection_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
```

The candidate is rejected.

## Failed Proof Surfaces

Old public replay:

| Surface | Rows | Base drops | Candidate drops | Gate |
| --- | ---: | ---: | ---: | --- |
| `m183_m168` | 16 | 16 | 15 | fail |
| `m183_m170` | 17 | 17 | 17 | pass |
| `m193_m189` | 14 | 14 | 14 | pass |
| `m212_m204` | 17 | 17 | 17 | pass |
| `m223_m219` | 17 | 17 | 16 | fail |
| `m267_m264` | 17 | 17 | 11 | fail |

Family-intersection replay:

| Gate | Rows | Base drops | Candidate drops | Gate |
| --- | ---: | ---: | ---: | --- |
| `short61049_to_candidate` | 25 | 25 | 17 | fail |
| `short61050_to_candidate` | 27 | 27 | 17 | fail |
| `short61051_to_candidate` | 27 | 27 | 17 | fail |

Source-diverse replay:

| Gate | Rows | Base drops | Candidate drops | Gate |
| --- | ---: | ---: | ---: | --- |
| `current_m333_surface` | 17 | 17 | 14 | fail |
| `m317_continuity_surface` | 17 | 17 | 13 | fail |
| `m314_continuity_surface` | 17 | 17 | 13 | fail |

Across the failed replay gates, normal-success deltas are `0.0` while success
drop counts decrease. This indicates the actor update is making wrong-history
rollouts safer, not causing a broad normal-history driving collapse.

## Generalization And Behavior

Fresh/OOD diagnostic results pass:

| Distribution | Seed | Base success | Candidate success | Margin delta |
| --- | ---: | ---: | ---: | ---: |
| fresh | 103900 | 0.867188 | 0.867188 | +0.002300 |
| fresh | 103901 | 0.871094 | 0.871094 | +0.002294 |
| moderate OOD | 103920 | 0.640625 | 0.640625 | +0.000036 |

Behavior gates pass on seeds `9505`, `9506`, `103930`, and `103931`; candidate
success equals base success and reset/zero-all ordering is retained.

## Interpretation

M1112 is a negative result with a useful failure mode:

```text
M1107 exact objective improvement survives;
the parameter/actor-input contract survives;
aggregate behavior and fresh/OOD diagnostics survive;
but replay-calibrated wrong-history proof surfaces wash out.
```

This means the M1107 materialized objective plus first-action/snippet anchors is
not sufficient to protect closed-loop wrong-history failure. The next step must
audit failed rows and design a wrong-history trajectory or replay-aware
retention mechanism before any new actor update, PPO, promotion, or private
holdout.

## Decision

```text
materialized_actor_update_full_public_gate_reject_proof_washout
```

Next milestone:

```text
m1113-v4-public-base-materialized-actor-update-proof-washout-audit
```
