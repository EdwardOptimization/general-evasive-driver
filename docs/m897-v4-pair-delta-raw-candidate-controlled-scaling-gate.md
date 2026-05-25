# M897 V4 Pair-Delta Raw-Candidate Controlled Scaling Gate

## Purpose

M897 executes the exact-first controlled scaling gate designed in M896 for the
larger raw objective-only candidates.

Candidates:

```text
m886_raw: runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
m891_raw: runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
```

Baseline:

```text
m568_base: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M897 does not train, run PPO, or promote a checkpoint.

## Exact Recheck

Runs:

```text
runs/m897_m886_raw_exact_recheck
runs/m897_m891_raw_exact_recheck
```

Both exact rechecks pass:

```text
candidate  result_class                                      rows     missing  finite  ppo  promoted  actor_changed
m886_raw   v4_enriched_pair_delta_objective_sanity_pass       247/247  0        true    no   no        false
m891_raw   v4_enriched_pair_delta_objective_sanity_pass       247/247  0        true    no   no        false
```

Objective loss means:

```text
m886_raw: 1.7950931260672298
m891_raw: 1.7950907494897872
```

## First Replay Gates

Run:

```text
runs/m897_raw_controlled_scaling_first_replay_gate
```

All four first replay gates passed:

```text
surface        rows  candidate_drops  normal_margin_delta  margin_gap_delta  pass
m886 M183/M170 17    0                +0.0003415019        +0.0000002201    true
m886 M267/M264 17    0                +0.0009072832        -0.0000001638    true
m891 M183/M170 17    0                +0.0003425226        +0.0000002185    true
m891 M267/M264 17    0                +0.0009098852        -0.0000001661    true
```

Aggregate:

```text
replay_gate_count: 4
replay_gates_passed: 4
replay_gates_failed: 0
overall_pass: true
failure_types: none
actor_inputs_changed: false
```

## Full Replay Gates

Run:

```text
runs/m897_raw_controlled_scaling_full_replay_gate
```

All twelve replay/proof gates passed:

```text
candidate  surface    rows  candidate_drops  normal_margin_delta  margin_gap_delta  pass
m886_raw   M183/M168  16    0                +0.0003244395        +0.0000002528    true
m886_raw   M183/M170  17    0                +0.0003415019        +0.0000002201    true
m886_raw   M193/M189  14    0                +0.0008717123        -0.0000001082    true
m886_raw   M212/M204  17    0                +0.0009075189        -0.0000001624    true
m886_raw   M223/M219  17    0                +0.0009075173        -0.0000001579    true
m886_raw   M267/M264  17    0                +0.0009072832        -0.0000001638    true
m891_raw   M183/M168  16    0                +0.0003254055        +0.0000002502    true
m891_raw   M183/M170  17    0                +0.0003425226        +0.0000002185    true
m891_raw   M193/M189  14    0                +0.0008741037        -0.0000001171    true
m891_raw   M212/M204  17    0                +0.0009101241        -0.0000001662    true
m891_raw   M223/M219  17    0                +0.0009101202        -0.0000001668    true
m891_raw   M267/M264  17    0                +0.0009098852        -0.0000001661    true
```

Aggregate:

```text
replay_gate_count: 12
replay_gates_passed: 12
replay_gates_failed: 0
overall_pass: true
failure_types: none
actor_inputs_changed: false
```

## Behavior Retention

Runs:

```text
runs/m897_raw_controlled_scaling_behavior_seed9505
runs/m897_raw_controlled_scaling_behavior_seed9506
```

Per seed:

```text
seed  policy     success  termination  clearance_mean  return_mean
9505  m568_base  0.8125   0.1875       1.465080        69.604261
9505  m886_raw   0.8125   0.1875       1.469930        69.565640
9505  m891_raw   0.8125   0.1875       1.469946        69.565539
9506  m568_base  0.8125   0.1875       1.479410        69.919597
9506  m886_raw   0.8125   0.1875       1.484310        69.880671
9506  m891_raw   0.8125   0.1875       1.484326        69.880569
```

Aggregate candidate minus base:

```text
candidate  success_delta  termination_delta  clearance_delta       return_delta
m886_raw   0.0            0.0                +0.0048752873044910  -0.0387735323216489
m891_raw   0.0            0.0                +0.0048912667465527  -0.0388747505574472
```

Diagnostics:

```text
m886_raw_zero_all success_mean: 0.7250
m891_raw_zero_all success_mean: 0.7250
```

## Interpretation

M897 is a positive controlled scaling result:

```text
The two raw objective-only candidates preserve exact recheck, first replay,
full replay, and behavior-retention gates versus M568.
```

Compared with alpha `0.1`, raw candidates produce about `10x` larger movement:

```text
alpha_0.1 behavior clearance delta: about +0.00049
raw behavior clearance delta: about +0.00488
```

This is still not a driver-performance improvement claim:

```text
success and termination are unchanged;
return decreases slightly;
all replay surfaces are public workflow artifacts;
the branch is rooted in M568 diagnostic BC, not the public-gate driver base.
```

But M897 does show that the objective direction has more proof-safe movement
budget than alpha `0.1`.

## Decision

Decision:

```text
raw_candidate_controlled_scaling_gate_pass
```

Next:

```text
m898-v4-pair-delta-raw-scaling-gate-audit
```

M898 should decide whether the next route is:

```text
fresh-source/generalization probe,
scaling boundary search beyond raw,
public-base integration design,
or richer pair-delta corpus construction.
```

M898 must not run PPO or promote directly from M897.
