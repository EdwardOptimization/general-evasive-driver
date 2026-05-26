# M1016 V4 Public Base M1013 Exact-Candidate Preflight

## Purpose

M1016 materializes selected exact-but-branch-unsafe M1013 candidates and runs
only M267/M264 preflight calibration.

This milestone does not train, run PPO, run the full public replay stack, use
private holdout, change actor inputs, or promote.

## Result

```text
result_class: m1013_exact_candidate_preflight_metric_ordering_artifact
preflight_pass_count: 1 / 3
candidate_a_pass: false
materialization_contract_pass: true
training_started: false
ppo_used: false
promoted: false
```

All materialized candidates changed only `actor_mean.bias` and
`actor_mean.weight`; actor input signatures and non-actor checksums match the
M974 base.

## Preflight Summary

| candidate | lambda | alpha | success-drop count | failed rows | gate pass |
| --- | ---: | ---: | ---: | --- | --- |
| `m1013_lam0001_a020` | 0.001 | 0.2 | 15 / 17 | 6, 15 | false |
| `m1013_lam0030_a050` | 0.030 | 0.5 | 17 / 17 | none | true |
| `m1013_lam0001_a050` | 0.001 | 0.5 | 14 / 17 | 6, 11, 15 | false |

Candidate B, `m1013_lam0030_a050`, passes M267/M264 preflight:

```text
normal_success_delta: 0.0
normal_margin_mean_delta: -0.000074
margin_gap_mean_delta: 0.000031
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

## Active Rows

Candidate A, lowest M1011 branch loss among exact candidates, still fails rows
`6` and `15`:

```text
row 6 wrong margin:  0.000000382
row 15 wrong margin: 0.000114999
```

Candidate B, despite higher M1011 branch-trust loss, makes the active wrong
histories fail again:

```text
row 6 wrong margin:  -0.000252
row 11 wrong margin: -0.000325
row 15 wrong margin: -0.000112
row 16 wrong margin: -0.000662
```

Candidate C fails rows `6`, `11`, and `15`:

```text
row 6 wrong margin:  0.000177
row 11 wrong margin: 0.000089
row 15 wrong margin: 0.000325
```

## Interpretation

M1016 falsifies a simple magnitude-only branch trust interpretation.

M1011/M1013 used:

```text
||a_wrong_candidate - a_wrong_base||^2 / margin_slack^2
```

That residual is sensitive, but sign-blind. Candidate B moves the wrong-history
branch more than Candidate A in L2, but in a safer direction: wrong-history
margins become more negative and M267/M264 preflight passes. Candidate A moves
less, but pushes rows `6` and `15` across zero.

Therefore the current trust metric is useful as a detector but not sufficient
as an ordering objective.

## Decision

```text
m1013_exact_candidate_preflight_metric_ordering_artifact_route_to_signed_branch_metric_audit
```

Do not promote Candidate B yet. This was a calibration preflight only. The next
step should audit signed/outcome-aware branch metrics and decide whether to
replace L2 trust with a directional or replay-calibrated residual before any
full public replay or new scalar update.

Next:

```text
m1017-v4-public-base-signed-branch-metric-audit
```
