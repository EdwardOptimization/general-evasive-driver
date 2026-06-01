# M2180 Paper-Route Current-Sim Repeat-Readiness Branch Synthesis

- status: completed
- decision: `current_sim_repeat_readiness_synthesis_continue_to_metadata_extension_implementation`
- synthesis_decision: `continue`
- synthesis window: `M2175-M2179`
- training in M2180: `false`
- measured execution in M2180: `false`
- implementation in M2180: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2175-M2179 changed the current-sim branch from one-seed measured execution to a
repeat-ready, metadata-auditable plan:

```text
M2175:
  audited M2174 as complete measured execution:
    320 episodes;
    0 failures;
    metric completeness 0;
    guardrail 0.
  Classified the result as one-seed smoke evidence, not ranking-ready.
  Raw outcomes were offtrack-dominated:
    63 success;
    20 collision;
    237 offtrack noncompletion.

M2176:
  designed a 3-group training-seed repeat:
    repeat_0_existing = M2171/M2174;
    repeat_1_seed_21761;
    repeat_2_seed_21762.
  Preserved tasks, profile definitions, actor inputs, budget, and eval seed policy.

M2177:
  implemented repeat materialization;
  trained 14 new smoke checkpoints successfully;
  materialized 640 new repeat workload rows;
  checkpoint paths existing = 640;
  reset-control trained count = 0;
  guardrail = 0.

M2178:
  audited repeat materialization as clean;
  found measured-runner repeat metadata preservation gap.

M2179:
  designed optional repeat metadata preservation:
    repeat fields optional for non-repeat workloads;
    if any repeat field is present, all repeat fields must be complete and
    preserved in episode/failure rows.
```

## Supported Claims

Supported:

```text
The current-sim measured runner can execute the original 320-cell panel end to
end with zero runner failures.
```

Supported:

```text
The project now has two additional training-seed repeat groups materialized,
with checkpoint paths and same-repeat reset-control aliasing.
```

Supported:

```text
The next blocker is metadata plumbing, not checkpoint availability or runner
schema compatibility.
```

## Falsified or Unsupported Claims

Falsified:

```text
The one-seed M2174 aggregate is enough to rank profile families.
```

It is not enough because it is one training seed and offtrack-dominated.

Falsified:

```text
Repeat measured execution is ready immediately after M2177 materialization.
```

M2178 showed repeat metadata would be dropped by the current measured runner.

Still unsupported:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Failure Taxonomy Summary

Active limitations:

```text
seed_fragility / comparison_underpowered:
  M2174 has one training seed per trainable profile.

outcome_support_low_offtrack_dominated:
  M2174 raw outcomes are mostly offtrack noncompletion.

metric_artifact_prevention / metadata_preservation_gap:
  repeat workloads have repeat metadata, but the runner must preserve it before
  repeat rollout can be audited cleanly.
```

Closed blockers:

```text
checkpoint_path_missing:
  M2165 had 320 missing checkpoint paths;
  M2171 repaired the original panel;
  M2177 materialized 640 repeat workload rows with existing checkpoint paths.
```

## Public Gate Overfit Risk

Risk is medium.

Reasons:

```text
The branch still uses the public current-sim 40-spec panel.
M2174 showed strong apparent profile differences, but M2175 explicitly blocked
ranking from one seed.
The repeat plan expands evidence along a training-seed axis instead of tuning to
the observed winner-like profile.
```

Mitigation:

```text
preserve repeat metadata as first-class fields;
audit repeat measured execution before comparison;
keep profile definitions and eval seeds fixed;
do not rank until repeat results have per-seed variance.
```

## Next Branch Decision

Decision: `continue`.

Reason:

```text
The current blocker is narrow and infrastructural: repeat metadata preservation
inside the measured runner. Implementing it is necessary before repeat rollout
and does not optimize a fixed public behavior gate.
```

Immediate next milestone:

```text
m2181-paper-route-current-sim-repeat-measured-runner-metadata-extension-implementation
```

M2181 may implement the metadata patch and focused tests only. It must not run
real measured execution, rank profiles, claim paper-level evidence, make a
finite-window vs GRU verdict, or claim level3 self-identification.
