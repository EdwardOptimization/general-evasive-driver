# M898 V4 Pair-Delta Raw Scaling Gate Audit

## Purpose

M898 audits M897 and chooses the next route after the raw objective-only
candidates passed exact-first public proof gates.

M898 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## M897 Summary

M897 evaluated:

```text
m886_raw: runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
m891_raw: runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
```

Exact recheck:

```text
candidate  rows     missing  finite  ppo  promoted  actor_changed
m886_raw   247/247  0        true    no   no        false
m891_raw   247/247  0        true    no   no        false
```

First replay:

```text
first_replay_gates_passed: 4 / 4
failure_types: none
```

Full replay:

```text
full_replay_gates_passed: 12 / 12
failure_types: none
candidate_success_drop_regressions: 0
```

Behavior retention:

```text
candidate  success_delta  termination_delta  clearance_delta       return_delta
m886_raw   0.0            0.0                +0.0048752873044910  -0.0387735323216489
m891_raw   0.0            0.0                +0.0048912667465527  -0.0388747505574472
```

Zero-all diagnostic:

```text
m886_raw_zero_all success_mean: 0.7250
m891_raw_zero_all success_mean: 0.7250
```

## Supported Claims

M897 supports these claims:

```text
The raw objective-only candidates are exact-recheck clean.

The raw candidates preserve the registered public first replay and full replay
proof gates versus M568.

The raw candidates retain behavior success and termination on seeds 9505/9506.

The raw candidates produce about 10x larger clearance movement than alpha_0.1
while still preserving the tested public proof gates.
```

This is stronger than M889/M893 because it shows there is usable movement budget
beyond the conservative alpha `0.1`.

## Unsupported Claims

M897 does not support these claims:

```text
The raw candidates improve success rate.

The raw candidates generalize beyond public replay surfaces and behavior seeds.

The raw candidates should be promoted.

The raw candidates are safe PPO initialization points.

The objective-only direction is ready for public-base integration.
```

The success and termination metrics are still ties versus M568, and return is
slightly lower. The improvement is a clearance-margin movement on public
retention seeds, not a driver-performance breakthrough.

## Failure Taxonomy

`proof_washout`:

```text
Not observed in M897. Full replay gates pass 12/12.
```

`behavior_regression`:

```text
Not observed for success or termination. Return decreases slightly, so broad
performance claims remain blocked.
```

`objective_overfit`:

```text
Still high risk. All replay and behavior gates are public workflow artifacts.
```

`metric_artifact`:

```text
Reduced by exact-first replay execution. Still a risk if clearance movement is
overinterpreted as success improvement.
```

`contract_violation`:

```text
Not observed. The P0 human-view no-wheel actor contract remains unchanged.
```

## Route Decision

The next route should be a fresh/generalization design, not direct integration
or PPO.

Reason:

```text
Raw candidates now have enough proof-safe movement to justify a fresh
distribution check.

They still do not show success improvement, so scaling beyond raw or PPO would
be premature.

Public-base integration should wait until fresh/generalization evidence says
the movement is useful outside the public proof rows.
```

Decision:

```text
raw_scaling_gate_audit_route_to_fresh_generalization_design
```

Next:

```text
m899-v4-pair-delta-raw-scaling-fresh-generalization-design
```

M899 should design a no-training fresh/generalization benchmark comparing:

```text
m568_base
m886_a010
m891_a010
m886_raw
m891_raw
heuristic
random
```

The benchmark should pre-register:

```text
success/termination non-regression;
clearance-margin effect-size threshold;
return as diagnostic, not first-class success;
seed-delta mining if aggregate metrics are tied;
no private holdout use;
no PPO or promotion.
```

If fresh/generalization shows only tiny clearance movement and no success or
seed-level benefit, the next route should be richer/fresher pair-delta corpus
construction rather than more scaling.
