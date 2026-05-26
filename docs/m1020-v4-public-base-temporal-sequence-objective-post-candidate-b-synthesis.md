# M1020 V4 Public Base Temporal Sequence Objective Post Candidate B Synthesis

## Purpose

M1020 synthesizes M1010-M1019 after Candidate B passed the full public replay
gate. The goal is to decide whether to keep doing local temporal-objective
repair, pivot, or move Candidate B into a separate promotion/generalization
audit branch.

This is a process milestone only. It does not train, run PPO, use private
holdout, change actor inputs, or promote.

## Evidence Summary

M1010-M1011 designed and implemented a margin-slack-weighted wrong-branch
trust-region detector:

```text
base trust loss: 0.0
M1002 alpha 0.01 trust loss: 3.529714
M1002 alpha 0.20 trust loss: 1407.006193
primary row contribution fraction at alpha 0.01: 0.664516
primary rows: 6, 15
secondary rows: 11, 16
```

That detector was useful for sensitivity: it activated strongly on known
proof-washing candidates.

M1012-M1013 then used the detector as a strict branch-trust constraint inside
an actor_mean-only repair update:

```text
lambda_wrong_trust sweep: 0.001, 0.003, 0.01, 0.03
exact candidate count: 10
exact plus branch-trust candidate count: 0
changed parameters: actor_mean.bias; actor_mean.weight
non-actor parameters changed: false
PPO used: false
promotion: false
```

This produced a negative result under the strict unsigned branch-trust gate.

M1014-M1017 audited that negative result against closed-loop replay. The key
finding was that the unsigned branch L2 detector is not a valid candidate
ordering metric:

```text
Candidate A:
  lambda=0.001, alpha=0.2
  lower branch trust loss
  M267/M264 success-drop count: 15/17
  failed rows: 6, 15

Candidate B:
  lambda=0.030, alpha=0.5
  higher branch trust loss
  M267/M264 success-drop count: 17/17
  failed rows: none

Candidate C:
  lambda=0.001, alpha=0.5
  M267/M264 success-drop count: 14/17
  failed rows: 6, 11, 15
```

M1018-M1019 then designed and ran the full public gate for Candidate B:

```text
exact temporal retention: pass 1/1
M267/M264 preflight: pass 1/1
six public replay surfaces: pass 6/6
source-diverse diagnostics: pass 3/3
behavior seeds 9505/9506: pass
actor inputs changed: false
training/PPO/promotion/private holdout: false
```

## Supported Claims

The branch supports these claims:

```text
1. The margin-weighted wrong-branch residual is a useful sensitivity detector.
   It identifies near-cliff public proof rows where tiny action shifts can flip
   wrong-history outcome.

2. Strict unsigned branch-L2 is not a sufficient ordering or acceptance gate.
   It penalizes safe-direction and unsafe-direction wrong-branch changes
   equally.

3. Outcome-signed replay evidence can rescue a candidate that the unsigned
   detector would reject. Candidate B has larger wrong-branch action drift than
   Candidate A but preserves wrong-history failure in closed-loop replay.

4. Candidate B is a valid public-gate candidate: it passes exact temporal
   retention, all six public replay surfaces, source-diverse diagnostics, and
   behavior seeds without actor-input or non-actor parameter changes.

5. The current best next step is no longer another local branch-trust objective
   tweak. The evidence has advanced to promotion/generalization audit scope.
```

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. A strict unsigned branch-trust threshold is a reliable replay-validity gate.
   M1016 showed lower unsigned loss can fail while higher unsigned loss passes.

2. The M1013 negative result means all exact candidates are unusable. Candidate
   B passes full public replay.

3. M267/M264 preflight alone is enough for Candidate B. M1019 had to run exact
   retention, six public surfaces, source-diverse diagnostics, and behavior
   seeds before the candidate could advance.

4. Candidate B can be promoted immediately. M1019 is public proof evidence, not
   promotion, private holdout, or paper-level generalization evidence.

5. PPO continuation is admissible now. Candidate B still needs
   promotion/generalization audit before any PPO proposal.
```

## Failure Taxonomy Summary

Observed failure categories:

```text
proof_washout:
  M1013 exact candidates could not satisfy the strict unsigned branch-trust
  gate; exact-safe movement pushed active public proof rows outside the
  detector threshold.

metric_artifact:
  M1016/M1017 showed the unsigned branch L2 metric orders candidates
  incorrectly because it has no outcome sign.

none:
  M1011 evaluator, M1016 materialization/preflight, and M1019 full public gate
  worked within their registered claim scopes.
```

No contract violation, behavior regression, training instability, private
holdout contamination, PPO washout, or promotion failure occurred in M1010-M1019.

## Public Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons:

```text
Candidate B has now passed six public proof surfaces plus source-diverse
diagnostics, so the result is stronger than a single-row proof pass.

However, all gates are still public. M267/M264 active rows directly influenced
the candidate-selection path through M1016/M1017, and Candidate B has not yet
been evaluated by a fresh promotion/generalization protocol.
```

Mitigation required before promotion:

```text
1. Keep proof, fresh public generalization, behavior ablation, and promotion
   decision separate.

2. Do not use private holdout in the first Candidate B promotion audit unless a
   holdout-rotation rule is explicitly registered.

3. Compare against the current M974 public base, not against stale M964/M399
   baselines.

4. If Candidate B fails fresh/generalization gates, classify the failure by
   tier before doing another objective update.
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close the local temporal-sequence objective repair loop for now:

```text
v4_public_base_temporal_sequence_objective
```

Open a new branch:

```text
v4_public_base_candidate_b_promotion_generalization
```

Rationale:

```text
M1019 gives enough public evidence to stop local objective repair and ask the
next-level question: whether Candidate B can become a new public-gate base
after a proper promotion/generalization audit. That audit must be separate from
the proof rows used to discover Candidate B.
```

Next ordinary milestone:

```text
m1021-v4-public-base-candidate-b-promotion-generalization-design
```

M1021 should design, but not run, a Candidate B promotion/generalization gate
with these tiers:

```text
Tier 0: checkpoint contract and exact temporal retention
Tier 1: six public replay proof retention
Tier 2: source-diverse protected diagnostics
Tier 3: fresh public randomized generalization
Tier 4: behavior and ablation seeds
Tier 5: promotion audit decision
```

## Decision

```text
temporal_sequence_objective_post_candidate_b_synthesis_promote_to_candidate_b_promotion_generalization
```
