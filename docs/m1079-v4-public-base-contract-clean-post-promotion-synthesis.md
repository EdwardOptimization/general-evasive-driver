# M1079 V4 Public Base Contract Clean Post Promotion Synthesis

## Purpose

M1079 synthesizes the `contract_clean_projection_promotion` branch after M1078
promoted the M1076 contract-clean projection checkpoint as the current
public-gate base.

This milestone does not train, run PPO, promote, or use private holdout.

## Evidence Summary

M1078 promoted:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Previous base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

The promotion evidence came from M1076:

```text
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
```

M1078 scoped the promotion to public-gate proof hardening only.

## Supported Claims

The current public-gate base is now a contract-clean projection checkpoint that
passes the expanded public gate stack.

The promotion is useful because M1069 showed that the previous base allowed an
8192-step PPO proposal to wash out wrong-history proof; M1076 hardens the active
proof surface without changing actor inputs or broad behavior metrics.

The next research branch should treat the promoted checkpoint as the new public
base for public-gate work.

## Falsified Claims

M1078 does not prove medium-PPO performance improvement. Success rates were
retained, not materially improved.

M1078 does not prove long-run PPO stability. The branch still showed that a
plain 8192-step PPO proposal needs projection or a stronger acceptance flow.

M1078 does not prove private-holdout or paper-level generalization. The
candidate was selected and validated using public artifacts.

## Failure Taxonomy Summary

```text
M1069: proof_washout
M1074: contract_violation
M1075-M1078: none
```

The post-promotion status is coherent: the public-gate base was updated after a
separate synthesis and promotion audit, and the scope limits remain explicit.

## Public Gate Overfit Risk

The new base was selected after several rounds of public proof-gate repair.
That is acceptable for a public-gate base, but it increases public-gate overfit
risk. The next PPO branch should not start from the new base until the current
base has a refreshed source-diverse protected/preference surface.

The refresh should mine new boundary rows under the promoted base rather than
only reusing M1072/M1073/M1076 active rows.

## Next Branch Decision

```text
synthesis_decision: promote_to_next_branch
closed_branch: contract_clean_projection_promotion
opened_branch: proof_hardened_base_surface_refresh
```

Next milestone:

```text
m1080-v4-public-base-proof-hardened-surface-refresh-design
```

M1080 should design a current-base source-diverse protected/preference surface
refresh before any new medium-PPO proposal. It should not run PPO or use private
holdout.
