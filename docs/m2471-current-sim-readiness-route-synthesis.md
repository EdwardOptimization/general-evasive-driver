# M2471 Current-Sim Readiness Route Synthesis

- status: completed
- synthesis decision: `pivot`
- decision: `pivot_to_high_fidelity_interface_preparation`
- manifest: `experiments/manifests/m2471-current-sim-readiness-route-synthesis.json`
- synthesis artifact: `docs/m2471-current-sim-readiness-route-synthesis.md`
- route plan: `docs/post-m2470-route-plan.md`
- superseded pending route: `m2471-paper-route-current-sim-dual-axis-stable-aes-distribution-support-materialization-preflight`
- next milestone: `m2472-high-fidelity-interface-hf0-design`
- reset/rollout/policy action in M2471: `false`
- measured execution in M2471: `false`
- repair/training/replay/PPO in M2471: `false`
- scenario/atlas/controller ranking in M2471: `false`
- winner selected: `false`
- actual-success improvement claim: `false`
- paper/FW-vs-GRU/level3 self-ID/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2452-M2470 moved the current-sim route from measured-outcome localization into
scenario-readiness infrastructure:

```text
M2452:
  artifact-only scenario-quality discriminant panel
  panel rows: 71
  scenario-quality blockers: 7
  possible repair-plan candidates: 19
  ranking/winner/guardrail violations: 0

M2455:
  scenario-quality protocol materialization
  candidate rows: 30
  stable-feasibility rows: 3
  stable-AES rows: 3
  guardrail violations: 0

M2458:
  reset/static preflight adapter
  work items: 30
  static checks: 246
  static failures: 0
  reset required: 6
  reset attempted: 0
  reset blocked by missing concrete overlays: 6

M2461:
  concrete overlay materialization/preflight
  concrete overlays: 6
  static failures: 0
  reset attempted: 0
  guardrail violations: 0

M2464:
  reset-only validation over the six concrete-overlay rows
  target rows: 6
  reset successes: 4
  reset failures: 2
  guardrail violations: 1

M2466:
  R1 stable-AES reset-sampling diagnostic panel
  reset attempts: 120
  reset successes: 20
  reset failures: 100
  baseline stable-AES: 5/24
  classification: seed_fragility

M2468:
  distribution-support atlas
  cells: 15
  reset-only attempts: 120
  reset successes: 109
  reset failures: 11
  stable_aes_support: 14/24
  stable-AES failures: 10/11 total reset failures
  guardrail violations: 0

M2469:
  accepted broad distribution support but kept measured readiness blocked
  because all three stable-AES cells remain partial.

M2470:
  design-only stable-AES distribution-support contract
  covers broad threshold-free 5/8, threshold-band 3/8, and low-mu near 6/8
  reset/rollout/policy action/repair/training/ranking/verdict: false
```

The old pending M2471 would have produced only static materialized rows from
the M2470 design. It explicitly would not reset, roll out, execute policy
actions, repair, train, rank, select a winner, or make any paper,
finite-window-vs-GRU, self-ID, training-repair, or current-sim verdict claim.

Paper-route axis classification:

```text
engineering driver performance:
  unchanged. No new closed-loop policy action or measured rollout occurred
  after M2445.

mechanism evidence for history dependence:
  unchanged. No wrong-history, reset-hidden, zero-history, finite-window, GRU,
  same-current, or different-history test occurred.

scenario/task-quality evidence:
  improved but still blocked. Current-sim now has better scenario-readiness
  accounting, concrete overlays, reset-only diagnostics, and a distribution
  atlas, but stable AES remains partial at 14/24.

high-fidelity validation readiness:
  improved at route level only. The project now has a reason to start interface
  preparation, not high-fidelity validation.

workflow or complexity reduction:
  positive. This synthesis stops a direct M2471/M2472/M2473 static artifact
  chain and opens a separate high-fidelity interface branch.
```

## Supported Claims

Supported:

```text
M2452-M2470 produced a clean current-sim scenario-readiness lineage.

The main current-sim blocker is not missing controller architecture; it is
scenario/readiness quality, especially stable-AES reset support.

M2470 is a valid design-only support contract, but executing direct static
materialization next would not change driver capability evidence.

The old M2471 materialization route is superseded by a process synthesis, not
falsified as technically invalid.

Current-sim should remain a fast diagnostic and mining layer.

High-fidelity interface preparation can start now as HF0 design while
preserving the deployable P0 human-view actor contract.
```

The supported claim is route discipline, not controller performance.

## Falsified Claims

Falsified or still blocked:

```text
Current-sim benchmark readiness is solved:
  blocked by partial stable-AES support and lack of a clean measured-readiness
  audit after M2470.

Stable-AES scenario readiness is solved:
  blocked because M2468 stable_aes_support remains 14/24 and all three
  stable-AES atlas cells are partial.

M2470 proves driver improvement:
  false. M2470 is design-only.

The old pending M2471 could change the paper verdict:
  false. It would only materialize static rows and explicitly forbids reset,
  rollout, policy action, repair, training, ranking, and verdict claims.

L0/L1/L2/L3 comparison is ready:
  blocked. The comparison still needs a stable benchmark pack and cannot be
  admitted from static or reset-only artifacts alone.

Level-3 self-ID is supported:
  blocked. No history-necessity test was run in this branch.
```

## Failure Taxonomy Summary

Observed or preserved:

```text
scenario_sampling_failure:
  stable-AES remains the live current-sim scenario-readiness blocker.

seed_fragility:
  M2466 classified R1 stable-AES reset sampling as seed-fragile, and M2468
  preserved stable-AES partial support at distribution level.

metric_artifact:
  soft-boundary and reset-only artifacts remain diagnostic unless validated by
  fresh measured execution.

local_search_guard risk:
  the branch has repeated design/materialization/audit/reset-only steps. The
  next direct static materialization would add process overhead without changing
  the paper-evidence state.
```

Not observed:

```text
contract_violation:
  labels and hidden dynamics remained metadata-only; actor inputs were not
  changed.

behavior_regression from training:
  no training or repair was run.

private holdout contamination:
  no private holdout was used.
```

## Public Gate Overfit Risk

Risk before synthesis: `high`.

Reason:

```text
The branch repeatedly works around public current-sim readiness artifacts. Even
the old pending M2471 would only convert a design into more static rows before
another audit.
```

Risk after synthesis: `medium`.

Mitigation:

```text
Direct static M2471 materialization is superseded.

Current-sim is frozen as a diagnostic layer unless a later synthesis approves
one bounded evidence-expanding reset-readiness attempt.

The next formal branch is HF0 high-fidelity interface design, which prepares a
validation boundary without claiming high-fidelity results.
```

Residual risk:

```text
HF0 is still design-only. It must route to an implementation/parity smoke before
any high-fidelity validation claim.
```

## Actual Progress Versus Process Overhead

Actual project capability changed:

```text
No controller capability changed in M2471. The project capability that changed
is workflow capability: the stale current-sim materialization route is stopped,
and a clean high-fidelity interface branch is registered.
```

Process overhead:

```text
high but necessary
```

Reason:

```text
The user explicitly stopped the stale current phase. The correct research
action is a durable route decision before another artifact-only milestone.
```

## Next Branch Decision

Synthesis decision:

```text
pivot
```

Route decision:

```text
freeze current-sim as diagnostic, allow at most one later bounded reset-readiness
attempt only after synthesis, and start high-fidelity interface preparation now
```

Closed branch:

```text
paper_route_current_sim_scenario_distribution_support_atlas
```

Next branch:

```text
high_fidelity_interface_preparation
```

Next milestone:

```text
m2472-high-fidelity-interface-hf0-design
```

M2472 should design only the HF0 boundary:

```text
DynamicsBackend reset/step/time interface
P0 observation extractor parity requirements
[steer, throttle, brake] action mapping
actuator latency and command-hold semantics
state extraction and hidden/oracle exclusion boundary
scenario taxonomy mapping contract
failure/status taxonomy
artifact and review boundaries
```

M2472 must not run current-sim reset, high-fidelity simulation, policy action,
rollout, training, replay, PPO, controller ranking, winner selection, or any
paper/high-fidelity/current-sim verdict.

## Blocked Routes

Blocked:

```text
direct execution of the old M2471 static materialization route
direct M2472 materialization result audit from old M2471
direct L0/L1/L2/L3 controller-family comparison from reset-only evidence
direct high-fidelity rollout before HF0 interface design and parity smoke
current-sim verdict from M2452-M2470
paper/self-ID/FW-vs-GRU verdict from M2452-M2470
```

Allowed:

```text
HF0 interface design as M2472
later current-sim bounded reset-readiness attempt only if a synthesis approves
using current-sim as diagnostic/mining layer
continuing paper route with self-ID as bounded falsifiable hypothesis
```
