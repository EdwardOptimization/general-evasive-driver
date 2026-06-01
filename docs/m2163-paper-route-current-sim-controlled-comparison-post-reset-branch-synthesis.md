# M2163 Paper-Route Current-Sim Controlled-Comparison Post-Reset Branch Synthesis

- status: completed
- decision: `current_sim_post_reset_branch_synthesis_continue_to_measured_execution_command_design`
- synthesis_decision: `continue`
- synthesis window: `M2158-M2162`
- reset rerun in M2163: `false`
- rollout/measured execution in M2163: `false`
- policy actions executed in M2163: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2158-M2162 closed the single reset blocker left by the first current-sim
controlled-comparison reset validation:

```text
M2158 ran a bounded reset-only diagnostic for m2151-current-sim-t5-03.
M2158 found original sequential eval seed 215335 fails at 200/800/1600 attempts.
M2158 found the materialized eval_seed_override 219103 passes at 200/800/1600 attempts.
M2159 audited the blocker as a seed-source protocol artifact.
M2160 froze the reset-validator repair: prefer per-spec eval_seed_override and log seed_source/actual_eval_seed.
M2161 implemented the repair and reran the full 40-spec reset-only validation.
M2161 passed with 40/40 reset success, seed_source_counts eval_seed_override:40, contract 0, metadata 0, forbidden-key 0, quota pass, guardrail 0.
M2162 audited the repaired reset pass as clean.
```

The actual capability change is not driver performance. It is scenario-panel
admissibility: the current-sim controlled-comparison panel is now reset-valid
under its materialized per-spec eval seeds.

## Supported Claims

Supported:

```text
The M2151 current-sim controlled-comparison panel has 40 executable specs and
320 planned workload rows with clean actor-input and metadata contracts.
```

Supported after M2161/M2162:

```text
The panel is reset-valid under materialized per-spec eval seeds:
reset_success_count == 40
reset_failure_count == 0
seed_source_counts == {eval_seed_override: 40}
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
```

Workflow-supported:

```text
The local-search guard correctly stopped direct command-design continuation
after six non-evidence milestones and forced this synthesis.
```

## Falsified Claims

Falsified:

```text
The M2154 failure means the T5 terminal-boundary spec is intrinsically
unresettable under the current template.
```

M2158 showed the spec resets at the original attempt budget when using its
materialized seed.

Falsified:

```text
Raising obstacle sample attempts is the primary repair.
```

The original sequential seed failed at higher budgets while the materialized
seed passed at budget 200.

Still unsupported:

```text
measured driver performance;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

No measured rollout or policy action has run in this post-reset branch segment.

## Failure Taxonomy Summary

Closed failure:

```text
scenario_sampling_failure:
  M2154 failed one T5 row during reset validation.

metric_artifact:
  The failure came from validator seed-source mismatch, not from the
  materialized executable spec's own deterministic reset seed.
```

No evidence of:

```text
contract_violation
forbidden actor input
profile-specific tuning
training instability
proof washout
behavior regression
```

Those categories are not active because this segment did not train, replay,
promote, or run measured policy behavior.

## Public Gate Overfit Risk

Risk is medium-low.

Reasons:

```text
the segment repairs a protocol artifact rather than optimizing policy behavior;
the reset validator now exposes seed provenance in every reset row;
the full 40-spec panel passed after repair rather than only the originally
failing row;
no controller family was tuned or ranked.
```

Remaining risk:

```text
all evidence is still public setup/reset evidence;
the measured runner may still require metadata compatibility work;
reset validity does not imply behavior quality or self-identification.
```

Mitigation:

```text
continue only to measured-execution command design;
force runner compatibility to be explicit before execution;
defer all ranking and paper interpretation to measured result audit and later
denominator-backed comparison steps.
```

## Next Branch Decision

Decision: `continue`.

Reason:

```text
The reset/setup blocker is closed cleanly, and the next evidence increment must
produce measured rollout data over the fixed current-sim panel. The correct
next step is not direct execution; it is a command design that checks whether an
existing runner preserves M2151 current-sim metadata or whether a focused
current-sim runner is required.
```

Immediate next milestone:

```text
m2164-paper-route-current-sim-controlled-comparison-measured-execution-command-design
```

M2164 may design the measured execution command or compatibility repair route.
It must not run measured execution, rank controller families, select a winner,
claim paper-level evidence, make a finite-window vs GRU verdict, or claim
level3 self-identification.
