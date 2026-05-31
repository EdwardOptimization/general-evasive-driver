# M2074 Paper-Route Outcome-Supported Decisive Repaired Reset Validation Result Audit

- status: completed
- decision: `route_to_seed_robust_obstacle_filter_repair_design`
- audited artifact: `runs/m2073_paper_route_outcome_supported_decisive_repaired_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`, `seed_fragility`
- operational subtype: `task_materialization_seed_overfit`
- reset/rollout/measured execution in M2074: `false`
- policy actions executed in M2074: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2073 improved the repaired reset panel substantially but did not validate it:

```text
M2066 original reset success: 0/240
M2070 no-reset repaired feasibility scan: 240/240 scenario-filter feasible
M2073 fresh-seed reset success: 164/240
M2073 fresh-seed reset failures: 76/240
```

The remaining failures are localized:

```text
error class: RuntimeError failed to sample an obstacle scenario matching the configured filters
contract violations: 0
metadata missing: 0
forbidden-key violations: 0
guardrail violations: 0
observation dimension failures among successful resets: 0
warmup max-active-step failures: 0
```

This is not a controller failure and not a self-identification result. No policy
action or rollout was executed.

## Failure Distribution

Failure by task family:

```text
T1_reactive_active_safety: 17/48
T2_same_current_different_older_history: 18/60
T3_active_diagnostic_warmup: 23/60
T4_variable_diagnostic_delay: 11/36
T5_terminal_boundary_near_constraint: 7/36
```

Failure by split:

```text
public_debug: 50/144
public_gate: 26/96
```

Failure by dynamics band:

```text
actuator_delay: 21/60
low_mu: 12/60
mixed_mu: 21/60
nominal_mu: 22/60
```

The highest-risk axes are obstacle geometry rather than contract metadata:

```text
late obstacle distance band: 45/80 failures
generous road width band: 45/80 failures
moderate curvature band: 45/80 failures
low initial speed band: 45/80 failures
```

Source-kind concentrations:

```text
delayed_obstacle_reveal_response: 5/6
curved_road_reactive_evasion: 6/8
long_delay_steer_lag_evidence: 4/6
same_current_yaw_authority_older_history: 8/10
warmup_brake_authority_probe: 8/10
```

All failed rows still use `max_threshold_score: 0.25`. The `15` rows that M2070
relaxed to `max_threshold_score: 1.0` all reset successfully in M2073. This is
consistent with the diagnosis that exact repaired obstacle windows are too
narrow for fresh reset RNG states.

## Interpretation

M2070 repaired each generated task to a deterministic feasible point/window
under the earlier reset-failure seed context. M2073 changed the eval seed base
to `207300` and exposed that some point windows are not seed-robust.

Supported interpretation:

```text
The panel is structurally closer to reset-valid than M2066.
The warmup-gate repair is holding.
The remaining blocker is seed-robust obstacle filter feasibility.
```

Rejected interpretation:

```text
The repaired 240-spec panel is reset-valid.
The generated rows are ready for measured execution.
The failures say anything about controller performance.
The failures say anything about finite-window vs GRU or level3 self-ID.
```

## Route Decision

Selected:

```text
M2075 seed-robust obstacle-filter repair design
```

The next repair must not repeat the M2070 mistake of preserving only a
single-seed feasible point. It should design a no-rollout repair protocol that
requires each repaired spec to pass a bounded multi-seed feasibility scan before
reset validation is rerun.

Required design properties:

```text
multi-seed support scan per spec;
explicit pass threshold such as K-of-N feasible reset seeds;
bounded distance and half-width window relaxation;
explicit max-threshold-score escalation policy;
source-kind and family quota preservation;
no policy action, rollout, measured execution, training, replay, or ranking;
no weakening of human-view actor-input contract or claim guards.
```

Rejected:

```text
direct measured execution:
  rejected because reset success is 164/240, not 240/240.

panel reduction:
  rejected for now because failures are distributed and repairable-looking,
  not isolated to one invalid source family.

rerun with another seed:
  rejected because that would test luck, not robustness.

another exact single-seed repair:
  rejected because M2073 already falsified single-seed feasibility as enough.
```

## Next

Next milestone:

```text
m2075-paper-route-outcome-supported-decisive-seed-robust-obstacle-filter-repair-design
```
