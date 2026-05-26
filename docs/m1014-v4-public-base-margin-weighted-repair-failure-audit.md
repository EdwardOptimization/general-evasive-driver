# M1014 V4 Public Base Margin-Weighted Repair Failure Audit

## Purpose

M1014 audits the M1013 negative result before any threshold relaxation, new
actor update, replay promotion, or PPO continuation.

This milestone does not train, optimize, run PPO, run replay gates, use private
holdout, change actor inputs, or promote.

## M1013 Summary

```text
result_class: margin_weighted_branch_repair_update_branch_trust_blocked
exact_candidate_count: 10
exact_and_branch_candidate_count: 0
changed parameters: actor_mean.bias, actor_mean.weight
non-actor changed: false
ppo_used: false
promoted: false
```

The failure is not a contract failure. M1013 did exactly what it was allowed to
do: update only `actor_mean` and evaluate exact temporal plus M1011 branch
trust gates.

## Exact Versus Trust Split

Per coefficient:

| lambda_wrong_trust | exact candidates | branch-trust candidates | joint candidates |
| ---: | ---: | ---: | ---: |
| 0.001 | 3 | 4 | 0 |
| 0.003 | 2 | 4 | 0 |
| 0.010 | 3 | 3 | 0 |
| 0.030 | 2 | 4 | 0 |

The split is clean:

```text
trust-safe candidates exist only at tiny alpha and do not reach temporal exact
improvement threshold.

exact candidates exist only at larger alpha and move rows 6 and 15 outside the
M1011 trust region.
```

Lowest-branch exact candidate:

```text
lambda_wrong_trust: 0.001
alpha: 0.2
total improvement: 0.001338
weighted branch trust loss: 1.325315
row 6 contribution: 0.467241
row 15 contribution: 0.721845
row 16 contribution: 0.078579
```

This is below the known failing M1002 alpha `0.01` total branch loss
`3.529714`, but row `15` contribution is actually higher than the M1002 alpha
`0.01` row `15` contribution `0.600505`. That makes immediate threshold
relaxation unsafe.

Best trust-safe point:

```text
lambda_wrong_trust: 0.030
alpha: 0.0025
total improvement: 0.00000951
weighted branch trust loss: 0.000165
exact_gate_pass: false
branch_gate_pass: true
```

This confirms the branch gate is reachable, but only at a movement scale that
does not improve the temporal objective enough.

## Failure Classification

Primary classification:

```text
proof_washout
```

Subclassification:

```text
exact_branch_active_set_conflict
```

Rejected explanations:

```text
contract_violation:
  rejected because only actor_mean changed and P0 actor inputs are untouched.

training_instability as primary:
  rejected as primary because exact candidates and trust-safe tiny-alpha points
  are both finite and interpretable.

metric_artifact as primary:
  rejected for now because M1011 detects the known M1002 alpha 0.01 replay
  washout, and the lowest-branch exact candidate still moves row 15 more than
  the known failing row 15 contribution.
```

Secondary concern:

```text
optimizer_instability_possible
```

Large `lambda_wrong_trust` runs show branch-loss oscillation in train history,
so future constrained updates may need line search or projection rather than
plain scalar joint training. This is secondary because even the clean
interpolation grid shows no exact+trust overlap.

## What Not To Do Next

Do not:

```text
1. Relax M1011 thresholds and call M1013 successful.
2. Add more lambda values blindly.
3. Widen the trainable surface before calibrating whether the trust metric is
   too conservative.
4. Start PPO from any M1013 candidate.
5. Promote or use private holdout.
```

## Next Route

Before changing the objective, run a replay-calibrated trust audit.

M1015 should materialize the lowest-branch exact M1013 candidates and run only
the M267/M264 preflight:

```text
candidate A:
  lambda 0.001, alpha 0.2
  lowest branch loss among exact candidates

candidate B:
  lambda 0.030, alpha 0.5
  best exact candidate from the strongest trust coefficient

candidate C:
  lambda 0.001, alpha 0.5
  stronger temporal improvement but larger branch drift
```

Decision rule:

```text
If all fail M267/M264 rows 6/15, M1011 trust gates are probably necessary and
the next route should be projection/line-search or synthesis before widening
the actor.

If any pass M267/M264 despite failing strict trust gates, M1011 thresholds are
too conservative and need replay-calibrated relaxation.
```

M1015 is still not promotion evidence. It is public proof calibration only.

## Decision

```text
margin_weighted_repair_failure_audit_route_to_replay_calibrated_trust_audit_design
```

Next:

```text
m1015-v4-public-base-m1013-exact-candidate-preflight-design
```
