# M2169 Paper-Route Current-Sim Measured-Readiness Repair Branch Synthesis

- status: completed
- decision: `current_sim_measured_readiness_repair_synthesis_continue_to_checkpoint_profile_materialization_design`
- synthesis_decision: `continue`
- synthesis window: `M2164-M2168`
- real M2151 measured execution in M2169: `false`
- policy actions executed in M2169: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2164-M2168 moved the current-sim branch from reset-valid setup into measured
readiness:

```text
M2164 checked runner compatibility and blocked direct measured execution:
  old measured runners use earlier panel metadata;
  M2151 workload has empty checkpoint_path for all rows.

M2165 implemented and ran a no-rollout readiness inventory:
  40 specs checked;
  320 workload rows checked;
  8 profiles checked;
  checkpoint_path_missing_count == 320;
  old_runner_missing_field_count == 12;
  guardrail_violation_count == 0.

M2166 audited the inventory and chose staged repair:
  runner adapter first;
  checkpoint/profile materialization second;
  real measured execution only after both are clean.

M2167 designed the current-sim measured runner adapter:
  preserve M2151 metadata;
  fake-rollout tests first;
  fail closed on missing checkpoints in real mode.

M2168 implemented the adapter:
  focused tests: 2 passed;
  fake-rollout metadata/aggregates pass;
  real-mode missing-checkpoint validation fails closed before rollout.
```

This branch segment repaired the runner-schema blocker. It did not repair the
checkpoint blocker.

## Supported Claims

Supported:

```text
The current-sim measured runner adapter exists and is focused-test covered.
```

Supported:

```text
The adapter preserves current-sim metadata and writes descriptive aggregates
under fake-rollout tests.
```

Supported:

```text
The adapter refuses real measured execution when required checkpoints are
missing, before environment rollout or policy action starts.
```

Still true:

```text
The M2151 panel remains reset-valid under materialized per-spec eval seeds.
```

## Falsified Claims

Falsified:

```text
The old measured runner can be reused directly for the current-sim panel.
```

M2165 found 12 missing required old-runner fields, and M2164 documented the
schema mismatch.

Falsified:

```text
Current-sim measured execution is ready immediately after reset validation.
```

All 320 workload rows still lack required checkpoints.

Still unsupported:

```text
real measured driver performance;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Failure Taxonomy Summary

Active blocker:

```text
checkpoint/profile materialization gap:
  checkpoint_path_missing_count == 320
  profile_ready_count == 0
```

Closed blocker:

```text
lineage_invalid / schema mismatch:
  old runner schema mismatch is no longer the primary blocker because a
  current-sim adapter now exists and has focused tests.
```

No evidence of:

```text
training instability
proof washout
behavior regression
metric overclaim
actor input contract violation
```

No training, replay, checkpoint promotion, or real measured rollout occurred in
this synthesis window.

## Public Gate Overfit Risk

Risk is low-to-medium.

Reasons:

```text
this branch segment is infrastructure, not policy optimization;
fake-rollout tests do not claim behavior;
missing-checkpoint validation prevents accidental real rollout;
the adapter preserves current-sim profile/history/task metadata.
```

Remaining risks:

```text
the real measured runner has not been exercised with trained checkpoints;
checkpoint training may introduce new fairness or seed-budget issues;
the final controller comparison still needs denominator-backed audit before
ranking or paper claims.
```

Mitigation:

```text
continue only to checkpoint/profile materialization design;
pre-register training budgets and seed policy before producing checkpoints;
do not run real measured execution until checkpoint paths and adapter audit are
clean.
```

## Next Branch Decision

Decision: `continue`.

Reason:

```text
The runner-schema blocker has an implemented adapter and focused tests. The
remaining measured-readiness blocker is checkpoint/profile materialization for
the 8 current-sim profile families. The next step should design that
materialization route, including training budget, seed policy, output paths,
and fairness constraints.
```

Immediate next milestone:

```text
m2170-paper-route-current-sim-checkpoint-profile-materialization-design
```

M2170 must design checkpoint/profile materialization. It must not train, run
real measured execution, rank controller families, select a winner, claim
paper-level evidence, make a finite-window vs GRU verdict, or claim level3
self-identification.
