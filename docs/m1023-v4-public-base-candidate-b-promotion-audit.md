# M1023 V4 Public Base Candidate B Promotion Audit

## Purpose

M1023 audits whether Candidate B should replace M974 as the current
public-gate base.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or claim paper-level/real-vehicle generalization.

## Candidate And Baseline

Promoted candidate:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Previous public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

## Evidence Reviewed

M1019 full public replay gate:

```text
exact_contract_pass_count: 1 / 1
M267/M264 preflight: 1 / 1
six public replay surfaces: 6 / 6
source-diverse diagnostics: pass 3 / 3
behavior seeds 9505/9506: pass
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

M1022 promotion/generalization gate:

```text
result_class: candidate_b_promotion_gate_candidate
exact_contract_pass_count: 1
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
reset_zero_all_ordering_retained: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Fresh public and moderate-OOD non-regression:

```text
fresh_public seed 102100:
  base success: 0.902344
  candidate success: 0.902344
  margin delta: +0.000035

fresh_public seed 102101:
  base success: 0.902344
  candidate success: 0.902344
  margin delta: +0.000037

moderate_ood seed 102120:
  base success: 0.664062
  candidate success: 0.664062
  margin delta: +0.000106
```

Behavior/ablation retention:

```text
seeds: 9505, 9506, 102130, 102131
normal success matches M974 on all seeds
normal >= reset >= zero_all ordering retained on all seeds
```

## Promotion Decision

Decision:

```text
promote_public_gate_base
```

Candidate B replaces M974 as the current public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Rationale:

```text
1. Candidate B preserves the P0 actor-input contract.
2. Only actor_mean.bias and actor_mean.weight differ from M974.
3. Exact temporal retention passes with positive total-loss improvement.
4. All six public proof replay surfaces pass.
5. Source-diverse protected diagnostics pass.
6. Fresh public and moderate-OOD evaluations do not regress M974.
7. Behavior/ablation retention passes.
8. The promotion is scoped to public-gate base status only.
```

## Scope Limits

This promotion does not claim:

```text
private holdout generalization;
paper-level statistical evidence;
real-vehicle transfer;
long-run PPO stability;
full scenario-distribution benchmark completion;
closed-loop self-identification proof beyond the registered public gates.
```

PPO remains blocked until a post-promotion synthesis/readiness milestone
decides the next controlled continuation protocol.

## Superseded Base

M974 becomes the previous public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M964 alpha `1.0` remains the older public-base lineage point, and M399 alpha
`0.05` remains an earlier lineage point.

## Next Blocker

After promotion, the next step is a post-promotion synthesis/readiness
milestone. It should decide whether to:

```text
1. run a guarded PPO readiness design from Candidate B;
2. refresh post-promotion proof surfaces first;
3. run additional public generalization before PPO;
4. stop and audit overfit risk.
```

## Decision

```text
candidate_b_promote_public_gate_base
```

Next:

```text
m1024-v4-public-base-candidate-b-post-promotion-synthesis
```
