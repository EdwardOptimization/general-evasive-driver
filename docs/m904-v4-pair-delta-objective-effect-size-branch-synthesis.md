# M904 V4 Pair-Delta Objective Effect-Size Branch Synthesis

## Purpose

M904 synthesizes the `v4_pair_delta_objective_effect_size` branch before any
public-base integration design, further scenario-family work, PPO, or promotion.

Covered milestones:

```text
M895-M903
```

M904 is synthesis-only:

```text
no benchmark execution
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Evidence Summary

M895 audited accepted alpha `0.1` and raw objective-only candidates:

```text
alpha_0.1 action_l2_mean_all: ~0.00012
raw action_l2_mean_all: ~0.00120
alpha_0.1 behavior clearance delta: ~+0.00049
raw behavior clearance delta: ~+0.00488
```

M896/M897 designed and executed controlled raw-candidate proof gates:

```text
exact rechecks passed: 2 / 2
first replay gates passed: 4 / 4
full replay gates passed: 12 / 12
behavior success/termination retained on seeds 9505/9506
```

M898 routed the raw scaling result to fresh public diagnostics rather than PPO
or promotion.

M899/M900 designed and executed an m121-style fresh benchmark:

```text
fresh seeds: 9705, 9706
episodes: 256 each
raw success_delta: 0.0
raw termination_delta: 0.0
raw clearance_delta: +0.003236 to +0.003250
seed-delta success flips: 0 improved, 0 regressed
```

M901 routed the margin-only fresh pass to a second scenario family.

M902/M903 designed and executed robust challenge-family benchmarks:

```text
near-threshold robust:
  raw success_delta: 0.0
  raw termination_delta: 0.0
  raw clearance_delta: about +0.00370

late high-energy robust:
  raw success_delta: 0.0
  raw termination_delta: 0.0
  raw clearance_delta: about +0.00337

seed-delta success flips: 0 improved, 0 regressed
```

## Supported Claims

The branch supports:

```text
Raw objective-only candidates provide a repeatable, larger movement budget than
the conservative alpha_0.1 candidates.

The raw movement preserves public exact, replay, and behavior-retention gates
versus the M568 diagnostic BC base.

The raw movement is margin-positive on an m121-style fresh public diagnostic
distribution.

The raw movement is also margin-positive on robust near-threshold and late
high-energy challenge families.

Across M897, M900, and M903, raw candidates do not regress success or
termination versus M568.
```

This is a real improvement over fixed proof-row tuning: the signal survives
multiple public diagnostic distributions.

## Falsified Claims

The branch falsifies or weakens:

```text
alpha_0.1 is large enough to support useful behavior claims.

raw objective-only movement necessarily washes out public proof gates.

public proof-gate retention alone is enough to judge usefulness.

raw candidates already improve success rate.

raw candidates can be promoted directly.

raw candidates are ready for PPO.
```

The success signal remains absent:

```text
success flips observed in M900/M903 seed-delta audits: 0
```

## Failure Taxonomy Summary

`proof_washout`:

```text
Not observed for raw candidates under M897 public replay gates.
```

`behavior_regression`:

```text
Not observed for success or termination in M897, M900, or M903. Return drops
slightly and remains diagnostic risk.
```

`metric_artifact`:

```text
Reduced by fresh and challenge diagnostics, but still present if margin-only
movement is overinterpreted as success improvement.
```

`objective_overfit`:

```text
Reduced relative to public proof rows because the signal survives fresh and
challenge public diagnostics. Still present because all evaluations remain
public workflow artifacts and rooted in M568 diagnostic BC.
```

`scenario_sampling_failure`:

```text
Not observed in M900 or M903.
```

`contract_violation`:

```text
Not observed. The P0 human-view no-wheel actor contract remains unchanged.
```

`lineage_invalid`:

```text
Not observed. The branch clearly roots candidates in M568 diagnostic BC and
does not treat them as public-base driver checkpoints.
```

## Public Gate Overfit Risk

Public overfit risk remains moderate:

```text
The branch now has more than fixed proof-row evidence, but all diagnostics are
still public and the candidate is rooted in M568, not the current public-gate
base.
```

Controls required before stronger claims:

```text
Do not promote M568-rooted raw candidates.
Do not run PPO from them as if they were public-base checkpoints.
Do not claim success improvement.
Design public-base integration separately.
Require exact/replay/behavior/fresh gates after any public-base transfer.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close current branch:

```text
v4_pair_delta_objective_effect_size
```

Open new branch:

```text
v4_pair_delta_public_base_integration_readiness
```

Next milestone:

```text
m905-v4-pair-delta-public-base-integration-readiness-design
```

Rationale:

```text
The objective direction is now strong enough to justify asking whether it can
be transferred toward the current public-gate base. It is not strong enough to
justify direct promotion or PPO.
```

M905 should design the public-base integration-readiness route:

```text
identify the current public-gate base;
define exact no-update compatibility checks;
define objective-only public-base probe rules;
define replay/behavior/fresh gates required after any public-base update;
keep PPO and promotion blocked.
```
