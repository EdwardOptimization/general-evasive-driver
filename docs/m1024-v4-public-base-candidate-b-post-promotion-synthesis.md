# M1024 V4 Public Base Candidate B Post Promotion Synthesis

## Purpose

M1024 synthesizes the Candidate B promotion branch after M1023 promoted
Candidate B as the current public-gate base.

This is a process milestone only. It does not train, run PPO, use private
holdout, change actor inputs, or make paper-level claims.

## Evidence Summary

M1021 designed a separate promotion/generalization protocol instead of
promoting Candidate B directly from M1019.

M1022 ran that protocol and passed:

```text
result_class: candidate_b_promotion_gate_candidate
exact_contract_pass_count: 1
proof_replay_gates_passed: 6
source_diverse_pass: true
fresh_generalization_comparison_count: 2
ood_generalization_comparison_count: 1
generalization_pass: true
behavior_seed_count: 4
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

M1023 promoted Candidate B:

```text
new public-gate base:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt

previous public-gate base:
  runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Promotion scope:

```text
public-gate base only
no private holdout
no paper-level claim
no real-vehicle claim
no PPO continuation yet
```

## Supported Claims

The branch supports these claims:

```text
1. Candidate B is a valid public-gate base successor to M974.

2. Candidate B preserves the P0 actor-input contract and changes only
   actor_mean.bias and actor_mean.weight relative to M974.

3. Candidate B preserves exact temporal evidence, public proof replay,
   source-diverse protected diagnostics, fresh public behavior, moderate-OOD
   behavior, and behavior/ablation ordering.

4. Promotion discipline worked: Candidate B was not promoted from M267/M264
   preflight or M1019 alone; it went through a separate promotion/generalization
   gate and a separate promotion audit.
```

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. Candidate B can be dismissed because the unsigned branch-L2 trust metric was
   large. Closed-loop replay and promotion/generalization gates both passed.

2. Candidate B can be promoted directly from a single proof surface. It needed
   M1019 full replay, M1022 fresh/generalization, and M1023 audit.

3. PPO can start immediately after promotion. A post-promotion readiness design
   with rollback and proof-retention criteria is still required.

4. Public-gate promotion is paper-level evidence. It remains public-gate status
   only.
```

## Failure Taxonomy Summary

Observed failure categories in this branch:

```text
none:
  M1021 design, M1022 promotion/generalization gate, and M1023 promotion audit
  all passed within their registered scopes.
```

Residual risks:

```text
public_gate_overfit_risk:
  Candidate B was discovered through public proof-row repair logic, so the next
  PPO step must be guarded by proof retention and fresh behavior checks.

promotion_scope_risk:
  The new base is stronger as public-gate evidence, but it is not yet a
  paper-level or private-holdout result.
```

No contract violation, behavior regression, scenario-sampling failure,
training instability, private holdout contamination, or PPO washout occurred.

## Public Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons:

```text
Candidate B came from public temporal/proof-row repair work.

M1022 reduced overfit concern with fresh public seeds, moderate-OOD seed,
source-diverse diagnostics, and behavior ablations.

However, those checks are still public and were run after Candidate B was
selected.
```

Mitigation required before any PPO continuation:

```text
1. PPO must be treated as a proposal, not a promotion.

2. The readiness design must include exact temporal retention, six public proof
   replay surfaces, source-diverse diagnostics, fresh public generalization,
   behavior/ablation checks, and rollback criteria.

3. Any PPO failure must be classified by tier and must not trigger longer PPO
   on the same recipe.

4. Private holdout remains unused unless a separate holdout-governance and
   rotation rule is registered.
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close branch:

```text
v4_public_base_candidate_b_promotion_generalization
```

Open branch:

```text
v4_public_base_candidate_b_guarded_ppo_readiness
```

Rationale:

```text
Candidate B is now the public-gate base. The next research question is whether
PPO can improve or at least preserve this base without washing out proof rows,
fresh public behavior, or behavior/ablation ordering.
```

Next ordinary milestone:

```text
m1025-v4-public-base-candidate-b-guarded-ppo-readiness-design
```

M1025 should design a guarded PPO readiness protocol before any PPO run. It
should specify:

```text
base checkpoint: Candidate B
proposal size: smoke-scale only
exact temporal retention gates
six public replay gates
source-diverse diagnostics
fresh public and moderate-OOD evals
behavior/ablation seeds
rollback criteria
no private holdout
no promotion from PPO smoke
```

## Decision

```text
candidate_b_post_promotion_synthesis_promote_to_guarded_ppo_readiness
```
