# M1077 V4 Public Base Medium PPO Readiness Synthesis

## Purpose

M1077 synthesizes the `expanded_gate_medium_ppo_readiness` branch after the
workflow cadence trigger. It covers M1068-M1076 and does not train, run PPO,
promote, or use private holdout.

## Evidence Summary

M1068 designed a conservative 8192-step medium-ramp PPO proposal from the M1049
public-gate base under the expanded exact, old public replay, M1061
family-intersection, source-diverse, fresh/OOD, and behavior gate stack.

M1069 ran that proposal. PPO completed with finite training metrics and broad
fresh/OOD plus behavior gates passed, but exact, old public replay,
family-intersection, and source-diverse proof gates failed. This was a useful
negative result: aggregate behavior was stable, but wrong-history branches
became marginally safe.

M1070 audited M1069 as coupled `proof_washout`, not training instability,
actor-input violation, broad generalization regression, or behavior regression.

M1071-M1073 converted the failure into a projection-first repair path:

```text
M1071: projection design
M1072: 22 failed rows across 8 proof surfaces exported as source-labeled corpus
M1073: no-PPO projection found first-replay-safe candidates
```

M1074 showed that the first selected `line` candidate fixed closed-loop proof
gates but violated the allowed changed-parameter surface because it inherited
broad PPO movement. This was classified as `contract_violation`, not
proof washout.

M1075 audited the M1073 projection table and found 13 exact-pass
contract-clean candidates. It selected:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

M1076 ran the full expanded public gate on that contract-clean candidate. It
passed:

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

## Supported Claims

The expanded proof stack is necessary. M1069 would look acceptable under broad
fresh/OOD and behavior gates, but expanded proof gates caught the wrong-history
regression.

The M1069 medium-PPO direction is not directly acceptable. PPO can still
complete and produce stable aggregate behavior while washing out self-ID proof.

The failed-row projection path is useful. M1072-M1076 produced a contract-clean
candidate that passes exact, public replay, family-intersection, source-diverse,
fresh/OOD, and behavior gates without changing actor inputs.

The M1076 candidate is best described as proof-base hardening. It retains
success rates and gives small positive fresh/OOD margin deltas, but it does not
establish a broad performance lift.

## Falsified Claims

The branch falsifies the claim that the current 8192-step guarded PPO recipe can
be lengthened or repeated directly after one run. It first needs post-step
projection, a stronger trust region, or a different PPO acceptance flow.

It falsifies the claim that broad generalization/behavior gates alone are
sufficient for self-identification evidence.

It falsifies the claim that the M1074 selected `line` candidate is contract
clean. Closed-loop gates passed, but disallowed parameter groups moved.

It does not prove medium-PPO performance improvement, paper-level
generalization, private-holdout robustness, or long-run stability.

## Failure Taxonomy Summary

```text
M1069: proof_washout
  exact active-set contract failed;
  old public replay, M1061 family-intersection, and source-diverse gates failed;
  broad generalization and behavior passed.

M1074: contract_violation
  closed-loop gates passed;
  allowed changed-parameter surface failed.

M1075-M1076: none
  contract-clean candidate selected and full public gate passed.
```

No milestone in this branch used private holdout. M1076 did not promote.

## Public Gate Overfit Risk

The evidence remains public-gate evidence. M1075 selected a candidate after
looking at M1073/M1074 public artifacts. Therefore M1076 is a valid public-gate
base-hardening result, but not an unbiased paper-level result.

Before making paper-level or private-holdout claims, the project still needs
fresh protected/preference surfaces, private holdout discipline, and broader
scenario-distribution evaluation.

## Next Branch Decision

```text
synthesis_decision: promote_to_next_branch
closed_branch: expanded_gate_medium_ppo_readiness
opened_branch: contract_clean_projection_promotion
```

The next milestone should be a separate promotion audit:

```text
m1078-v4-public-base-contract-clean-projection-promotion-audit
```

That audit may promote the M1076 checkpoint only as a public-gate
proof-hardened base. It must not claim medium-PPO performance improvement,
private-holdout evidence, paper-level generalization, or long-run PPO stability.
