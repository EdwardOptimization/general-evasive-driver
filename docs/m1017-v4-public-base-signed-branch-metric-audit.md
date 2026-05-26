# M1017 V4 Public Base Signed Branch Metric Audit

## Purpose

M1017 audits the M1016 metric-ordering artifact.

This milestone does not train, run PPO, run replay gates, use private holdout,
change actor inputs, or promote.

## M1016 Conflict

M1016 found:

```text
Candidate A: lambda 0.001, alpha 0.2
  M1011 branch trust loss: 1.325315
  M267/M264 success-drop count: 15/17
  failed rows: 6, 15

Candidate B: lambda 0.030, alpha 0.5
  M1011 branch trust loss: 6.986220
  M267/M264 success-drop count: 17/17
  failed rows: none

Candidate C: lambda 0.001, alpha 0.5
  M1011 branch trust loss: 8.282467
  M267/M264 success-drop count: 14/17
  failed rows: 6, 11, 15
```

Candidate B has larger unsigned branch action drift than Candidate A, but
passes replay. Candidate A has lower unsigned drift, but fails rows `6` and
`15`.

## Active-Row Evidence

Candidate A wrong-history replay:

| row | wrong margin | success drop |
| ---: | ---: | --- |
| 6 | 0.000000382 | false |
| 11 | -0.000160 | true |
| 15 | 0.000115 | false |
| 16 | -0.000404 | true |

Candidate B wrong-history replay:

| row | wrong margin | success drop |
| ---: | ---: | --- |
| 6 | -0.000252 | true |
| 11 | -0.000325 | true |
| 15 | -0.000112 | true |
| 16 | -0.000662 | true |

Candidate C wrong-history replay:

| row | wrong margin | success drop |
| ---: | ---: | --- |
| 6 | 0.000177 | false |
| 11 | 0.000089 | false |
| 15 | 0.000325 | false |
| 16 | -0.000227 | true |

The replay evidence explains the conflict:

```text
Candidate B moves the active wrong-history rollouts to more negative margins.
Candidate A and C move at least rows 6 and 15 across zero.
```

## Metric Diagnosis

The M1011 metric:

```text
||a_wrong_candidate - a_wrong_base||^2 / margin_slack^2
```

is useful as a sensitivity detector:

```text
It activates on the known M1002 alpha 0.01 proof-washing candidate.
```

But it is not a valid ordering gate by itself:

```text
It penalizes safe-direction and unsafe-direction action changes equally.
```

The right proof ordering is outcome-signed:

```text
wrong-history margin should remain negative on proof rows;
normal-history success and margin should not regress.
```

For future differentiable objectives, the branch term should become
outcome-aware or replay-calibrated, not pure action L2. Candidate B is evidence
that a larger action change can be safe if it moves the wrong-history branch in
the correct direction.

## Immediate Route

Candidate B passed the required M267/M264 preflight and should not be discarded
because of the unsigned metric artifact.

The next step should be a full public replay gate design for Candidate B:

```text
candidate:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt

required gates:
  six public replay surfaces
  exact temporal retention
  source-diverse protected diagnostics
  behavior seeds 9505/9506
  no actor input changes
```

This is still not promotion. It is the next proof/generalization gate after
M267/M264 preflight.

## Future Objective Note

If Candidate B fails later public replay, the next objective design should not
return to unsigned branch L2. It should use one of:

```text
1. replay-calibrated signed branch targets;
2. margin-direction labels from short closed-loop probes;
3. lexicographic projection: exact temporal improvement first, then restore
   M267/M264 margins by replay-aware repair.
```

## Decision

```text
signed_branch_metric_audit_route_to_candidate_b_full_public_replay_design
```

Next:

```text
m1018-v4-public-base-m1013-candidate-b-full-replay-design
```
