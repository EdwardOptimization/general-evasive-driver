# M2157 Paper-Route Current-Sim Controlled-Comparison Benchmark Branch Synthesis

- status: completed
- decision: `current_sim_controlled_comparison_branch_synthesis_continue_to_terminal_boundary_diagnostic`
- synthesis_decision: `continue`
- synthesis window: `M2147-M2156`
- reset rerun in M2157: `false`
- rollout/measured execution in M2157: `false`
- policy actions executed in M2157: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2147-M2156 moved the project from generated-proxy comparison scaffolding into
a current-simulator controlled-comparison setup:

```text
M2147 designed an 8-profile L0/L1/L2/L3 matrix and T1-T5 task-family plan.
M2148 materialized the benchmark contract preflight: 8 profiles, 5 task families, 18 metric rows, 10 explicit deferred gaps.
M2149 audited M2148 and blocked direct reset because those rows were not executable env specs.
M2150 designed executable spec materialization: 40 specs and 320 profile workload rows.
M2151 materialized those specs with contract 0, forbidden key 0, profile tuning 0, guardrail 0.
M2152 audited M2151 and admitted reset-validation command design.
M2153 froze the current-sim reset-only validation command.
M2154 implemented and ran reset validation: 39/40 success, 1 reset-sampling failure, no rollout or policy action.
M2155 audited the failure as one localized T5 terminal-boundary scenario_sampling_failure.
M2156 froze a bounded reset-only diagnostic over the failing row, but harness cadence requires synthesis before implementation.
```

The branch has produced one real current-sim reset result, not just process
docs. The result is useful but incomplete: the panel is not reset-valid yet
because `m2151-current-sim-t5-03` failed to sample an obstacle scenario under
the frozen reset seed.

## Supported Claims

Supported:

```text
The current-sim controlled-comparison benchmark has a concrete executable-spec
panel with 40 specs and 320 planned profile workload rows.
```

Also supported:

```text
The actor-input and metadata contract for the panel is clean:
contract_violation_count == 0
forbidden_key_violation_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0
```

Reset evidence supported:

```text
39/40 specs reset with finite 72-dimensional observations and initialized obstacles.
The single failed row is localized to T5_terminal_boundary_near_constraint.
The failure is a scenario_sampling_failure, not a schema or contract failure.
```

Process evidence supported:

```text
The harness caught an attempted direct continuation past synthesis cadence.
The branch now has an explicit synthesis checkpoint before more local reset work.
```

## Falsified Claims

Falsified or still unsupported:

```text
The full M2151 current-sim panel is reset-valid.
```

This is false until the T5 reset-sampling issue is repaired and rerun cleanly.

Still unsupported:

```text
measured driver performance;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

The current branch has not executed policy actions or measured rollout. It
therefore cannot say anything about driver quality, recurrent memory, finite
window sufficiency, or self-identification.

## Failure Taxonomy Summary

Active failure:

```text
scenario_sampling_failure:
  M2154 failed on one T5 terminal-boundary row:
  m2151-current-sim-t5-03, eval seed 215335.
```

Not active:

```text
contract_violation:
  contract_violation_count == 0.

metric_artifact:
  the failure is a real reset-sampling failure, not a stale quota mismatch.

training_instability / proof_washout / behavior_regression:
  no training, replay, PPO, rollout, or checkpoint update ran.
```

Workflow issue caught and repaired:

```text
local_search_guard:
  direct M2157 implementation would have exceeded branch cadence and
  consecutive non-evidence guard limits. This synthesis resets the branch
  discipline before implementation.
```

## Public Gate Overfit Risk

Risk is medium.

Reasons:

```text
the branch is still public-gate-only;
no private holdout is involved;
the evidence is mostly setup/reset feasibility, not behavior;
one T5 sampling failure shows the task panel is not yet robust;
continuing local reset repairs without synthesis would risk process drift.
```

Mitigation:

```text
continue only to a bounded diagnostic over the single failed row;
do not run measured execution until reset validity is repaired and audited;
do not rank profiles or make paper/self-ID claims from reset-only evidence.
```

## Next Branch Decision

Decision: `continue`.

Reason:

```text
M2156 diagnostic remains the highest-leverage next evidence increment because
it directly classifies the only blocker preventing reset validation:
seed-local sampling miss vs attempt-budget limitation vs terminal-boundary
template brittleness.
```

The continuation is bounded:

```text
target row: m2151-current-sim-t5-03
eval seeds: 215335, 219103
attempt budgets: 200, 800, 1600
diagnostic attempts: 6
rollout/policy actions: false
ranking/paper/self-ID claims: false
```

Immediate next milestone:

```text
m2158-paper-route-current-sim-terminal-boundary-reset-sampling-diagnostic-implementation-and-run
```

M2158 may implement and run only the reset-only diagnostic. It must not repair
the panel, rerun the full 40-spec reset gate, run measured execution, or compare
controller families. M2159 should audit the diagnostic result before any repair
or rerun.
