# M988 V4 Public Base Extreme Scenario Family Synthesis

## Evidence Summary

M984-M987 tested whether richer config-only scenario families would expose
source-diverse wrong-history outcome-sensitive rows for the M974 public-gate
base.

Results:

| Milestone | Role | Key result |
| --- | --- | --- |
| M984 | config smoke | 5 configs work; 211 snapshots; 57 near-boundary rows |
| M985 | broad source mining | 1137 snapshots; 246 near-boundary rows; 0 accepted |
| M986 | near-cliff mining | 60 near-cliff rows; 0 accepted |
| M987 | long-horizon audit | 20-step horizon; 39 near-cliff rows; 0 accepted |

Across M985-M987, action separation stayed live, but wrong-history rollouts
remained successful:

```text
M985 all-action-threshold rows: 15019, wrong success rate: 1.0
M986 all-action-threshold rows: 10431, wrong success rate: 1.0
M987 all-action-threshold rows: 7090, wrong success rate: 1.0
```

## Supported Claims

The M984 configs are valid infrastructure for broader stress testing. They
sample hidden-dynamics emergency scenarios without actor-input contract changes.

Config-only global randomization is not enough, by itself, to produce a
source-diverse wrong-history outcome-sensitive corpus around the current M974
public-gate base.

The negative result is not explained by missing near-cliff filtering or a
9-step continuation horizon. M986 and M987 tested both.

## Falsified Claims

The existing five global extreme scenario configs do not immediately solve the
source-diverse proof-surface problem.

Continuing the same mining branch with more of the same seeds/candidates is not
the highest-leverage next step.

The branch does not justify training, PPO continuation, promotion, or threshold
relaxation.

## Failure Taxonomy Summary

Primary taxonomy:

```text
scenario_sampling_failure
```

More precisely, this is not ordinary sampler failure. It is a scenario-family
expressivity failure for the current proof question: the configs produce
scenarios and action differences, but not outcome-sensitive wrong-history
failures.

## Public Gate Overfit Risk

Public-gate overfit risk remains `moderate`.

The current public base still has known public proof retention and one
repeatable isolated OOD pocket from M980/M982. However, M984-M987 show that the
new config families are not yet a durable source-diverse proof distribution.

## Next Branch Decision

Decision:

```text
pivot
```

Open a new branch:

```text
v4_public_base_capability_step_fault_generation
```

The next branch should add or design explicit hidden capability-step/fault
events rather than only static episode-level randomization.

Near-term supported by the current single-track model:

```text
global tire/lateral-authority drop
global brake-authority drop
global drive-authority drop
global actuator-lag step
global friction step already exists and should remain
```

Future dynamics extensions:

```text
split-mu
single-tire puncture
half-shaft failure
corner-specific brake loss
individual wheel failures
```

Those require asymmetric or multi-wheel dynamics and should not be claimed by
the current single-track branch.
