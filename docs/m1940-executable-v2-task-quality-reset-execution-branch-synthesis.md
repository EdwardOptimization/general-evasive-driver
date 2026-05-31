# M1940 Executable V2 Task-Quality Reset Execution Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- completed branch: `paper_route_task_quality_reset_execution`
- next branch: `paper_route_task_quality_measured_outcome_localization`
- decision: `task_quality_reset_execution_branch_synthesis_pivot_to_outcome_localization`
- reset/rollout/measured execution in M1940: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M1930-M1939 moved the redesigned task-quality panel from no-rollout specs to a
complete public diagnostic measured execution.

Branch progression:

```text
M1930: selected reset-only validation as the first execution stage
M1931: implemented focused reset validator, synthetic tests 3 passed
M1932: froze exact reset-only command
M1933: ran reset validation, 80/80 success, zero failures
M1934: audited reset pass and admitted measured execution design
M1935: found existing measured runners were not exact schema matches
M1936: implemented focused measured runner, synthetic tests 3 passed
M1937: froze exact 960-cell measured execution command
M1938: ran 960-cell measured execution, zero failures
M1939: audited measured result as complete but low-support/off-track-dominated
```

Material capability changed:

```text
before M1930:
  M1928 had 80 executable specs and 960 workload rows but no reset or rollout
  evidence.

after M1939:
  the same panel is reset-valid,
  has a metadata-preserving measured runner,
  has complete 960-row public diagnostic measured artifacts,
  and has a documented raw outcome blocker.
```

## Supported Claims

Supported infrastructure/task-quality claims:

- the M1928 `80`-spec public panel resets cleanly under the current simulator;
- reset validation preserved the strict human-view/no-wheel/no-oracle contract;
- the measured runner can execute the `80 x 12 = 960` public workload without
  row failures;
- profile, tier, role, surface, split, sampled label, and source metadata are
  preserved into measured artifacts;
- metric completeness and guardrails are clean;
- the public diagnostic panel has nonzero success support.

Supported measured-execution facts:

```text
episode_count: 960
failure_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
success_obstacle_pass: 40 / 960 = 4.17%
collision_failure: 105 / 960 = 10.94%
off_track_noncollision_noncompletion: 815 / 960 = 84.90%
```

## Falsified Or Unsupported Claims

Falsified for this branch:

```text
direct controller ranking readiness
```

Reason: outcome support is too low and off-track-dominated. The result is
diagnostic, not a robust comparison surface.

Still unsupported:

- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- high-fidelity validation readiness.

The profile-level pattern is interesting but not conclusive:

```text
L1_one_step: 15.00% success
L0_current_masked: 12.50%
L3_online_gru: 11.25%
L3_reset_control_corrected: 11.25%
all L2 window/current-tiled profiles: 0.00%
```

This should be localized before it is interpreted.

## Failure Taxonomy Summary

Current blocker:

```text
outcome_support_low_offtrack_dominated
```

Not current blockers:

```text
reset_sampling_failure
measured_runner_failure
metric_artifact
contract_violation
private_holdout_leak
controller_ranking_evidence
level3_self_id_evidence
```

The branch's process overhead was acceptable because it produced new execution
capability and new closed-loop data. But continuing with immediate local repair
would now become local search. The correct next step is a new branch with a
bounded no-rerun localization objective.

## Public Gate Overfit Risk

Current risk: `medium_high`.

Risk reducers:

- M1928 was a fresh panel from a 640-source redesign, not a repair of the old
  16-source fixed panel;
- M1933 and M1938 used frozen commands and preserved guardrails;
- private holdout rows were not used;
- positive and negative results were documented.

Remaining risks:

- all evidence is still public diagnostic, not holdout;
- the measured outcome surface is low-support and dominated by off-track rows;
- direct ranking could overfit to a small set of 40 successes;
- the apparent L1/L0/L3 versus L2 profile pattern could be a scenario/geometry
  artifact.

## Next Branch Decision

Decision:

```text
pivot
```

New branch:

```text
paper_route_task_quality_measured_outcome_localization
```

Next milestone:

```text
m1941-executable-v2-task-quality-measured-outcome-localization-design
```

M1941 should design a no-rerun localization pass over M1938 artifacts. It
should answer:

- where the 40 successes are concentrated;
- where off-track dominance comes from;
- whether the L2 zero-success pattern is profile-specific or scenario-specific;
- whether any slice has enough joint support for later comparison;
- whether the next branch should be task-quality repair, measured comparison
  design, or scenario redesign.

No new rollout, ranking, paper-level claim, or level3 self-ID claim is admitted
by this synthesis.
