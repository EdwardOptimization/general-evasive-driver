# M970 V4 Public Base Direction Target Actor-Fit Post-Promotion Synthesis

## Purpose

M970 synthesizes the M964-M969 direction-target actor-fit branch after M969
promoted alpha `1.0` as the new public-gate base.

Current public-gate base:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Previous public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

M970 does not train, run PPO, use private holdout, change actor inputs, or make
a paper-level claim.

## Evidence Summary

M964 implemented objective-only actor fitting on the exported M962
direction-target corpus:

```text
result_class: direction_target_actor_fit_candidate
candidate_alpha_count: 5
candidate_alphas: 0.05, 0.10, 0.20, 0.50, 1.00
target_fit_improved_count: 5
proof_preflight_pass_count: 5
retention_pass_count: 5
trainable surface: actor_mean only
ppo_used: false
```

M965 designed the no-training replay gate for the M964 candidates.

M966 implemented that gate:

```text
result_class: direction_target_actor_fit_replay_gate_pass
selected_alpha: 1.0
candidate_preflight_pass_count: 5 / 5
public_replay_gates_passed: 6 / 6
source_diverse_protected_status: pass
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

M967 designed a separate promotion/generalization layer so that public replay
success would not directly imply promotion.

M968 implemented that layer:

```text
result_class: direction_target_actor_fit_promotion_gate_candidate
proof_pass: true
generalization_pass: true
behavior_pass: true
source_diverse_protected_status: pass
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

Fresh public eval:

```text
seed 96700: success delta 0.0, margin delta -0.0005224
seed 96701: success delta 0.0, margin delta -0.0005119
```

Moderate OOD eval:

```text
seed 96720: success delta 0.0, margin delta 0.0005235
```

M969 audited the evidence and promoted alpha `1.0` as the current public-gate
base.

## Supported Claims

Supported:

- direction-target export plus actor-mean fitting produced a usable candidate;
- the candidate preserved the full public proof replay stack;
- M267/M264 wrong-history success-drop count stayed `17 / 17`;
- source-diverse protected diagnostics passed;
- behavior seeds retained normal/reset/zero-all ordering;
- fresh public randomized eval and moderate OOD eval showed no material
  non-regression failure;
- actor input contract remained P0 human-view/no-oracle/no-wheel;
- alpha `1.0` is justified as the new public-gate base.

## Falsified Claims

Falsified or explicitly not supported:

- actor-fit objective metrics alone are enough for promotion;
- public proof replay alone is enough for promotion;
- this branch proves paper-level private-holdout generalization;
- this branch proves real-vehicle transfer or high-fidelity four-wheel dynamics;
- this branch proves long PPO continuation from alpha `1.0` is safe;
- this branch proves the ideal driver objective is complete.

## Failure Taxonomy Summary

The earlier controlled-fusion branch failed mainly through:

```text
proof_washout
objective_overfit
metric_artifact
promotion_gate_failure
```

The direction-target actor-fit branch resolved the immediate blocker by:

```text
correcting target direction sign
exporting branch-separated proof and retention anchors
using actor_mean-only fitting
requiring full M267/M264 preflight over all candidate alphas
separating replay gate, generalization gate, and promotion audit
```

No M964-M969 milestone introduced:

```text
contract_violation
private_holdout_contamination
training_instability
seed_fragility at the checked public/fresh seeds
```

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons:

- direction targets originate from public low-tail/proof rows;
- public replay surfaces were repeatedly used as daily proof guards;
- fresh eval coverage is useful but still small relative to the intended
  driver distribution;
- moderate OOD coverage is a non-regression check, not a broad benchmark;
- no private holdout was used, by design.

Mitigation:

- keep M399 as comparison lineage;
- do not claim paper-level generalization from M966/M968;
- require future PPO to preserve M966/M968 gates;
- add broader fresh scenario and self-ID stress gates before larger claims;
- rotate any private holdout if it ever guides repair.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Open a new branch:

```text
v4_public_base_post_promotion_guarded_ppo_readiness
```

Next milestone:

```text
m971-v4-public-base-post-promotion-guarded-ppo-readiness-design
```

The next branch should design guarded PPO readiness from the newly promoted
alpha `1.0` public-gate base. It must not immediately run PPO. The first task is
to specify:

```text
base checkpoint: alpha_1_0
proposal PPO config
proof replay gates to retain
fresh generalization gates to retain
behavior/ablation gates to retain
exact post-PPO repair or rollback criteria
promotion/no-promotion decision rule
```

Only after that design is reviewed should a smoke-scale PPO proposal be
attempted.
