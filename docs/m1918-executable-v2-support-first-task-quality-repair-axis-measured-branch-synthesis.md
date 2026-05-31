# M1918 Executable V2 Support-First Task-Quality Repair-Axis Measured Branch Synthesis

- status: completed
- synthesis decision: `stop`
- next branch decision: `pivot_to_paper_route_task_quality_scenario_redesign`
- branch synthesized: `paper_route_repair_axis_measured_wrapper`
- evidence window: M1909-M1917
- reset/rollout/measured execution in M1918: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## evidence_summary

M1909-M1917 successfully moved the task-quality repair-axis work from a
no-rollout matrix into a complete measured panel:

```text
M1909: measured-wrapper extension points implemented; mocked tests passed
M1910: exact measured command and target counts fixed
M1911: measured CLI mode and base-spec binding implemented; mocked tests passed
M1912: first measured execution incomplete; 192 sampling failures
M1913: failures localized to road_geometry_fixed obstacle-delta mapping
M1914: mapping repair implemented; focused tests passed
M1915: repaired rerun complete; 1536 rows, 0 failures, 0 guardrail violations
M1916: result audit found complete and balanced panel, but raw success 0
M1917: full-panel no-rerun localization; all 1536 rows classified
```

M1917's localized outcome surface is the decisive evidence:

```text
joint_clearance_containment: 0
clearance_only_offtrack: 1257
containment_collision: 261
collision_and_offtrack: 18
near_miss_rows: 644
```

The branch therefore produced strong infrastructure and scenario-diagnostic
evidence, but it did not produce an interpretable controller-comparison or
paper-level result.

## supported_claims

Supported:

- the measured-wrapper execution path can materialize the registered
  task-quality repair-axis panel;
- the M1912 sampling failure was a localized wrapper/config mapping issue and
  is repaired;
- all M1915 rows can be classified into a consistent
  clearance/containment/near-miss taxonomy without rerun;
- the current repair-axis panel exposes a broad task-quality conflict:
  obstacle clearance generally trades off against road containment;
- near-miss rows are abundant enough to guide a broader scenario redesign.

Unsupported:

- any controller-family ranking;
- task-quality repair success;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## falsified_claims

Falsified or weakened by M1917:

- local repair-axis deltas around the M1902/M1895 source set are sufficient to
  create joint clearance-containment outcomes;
- raw binary success on this panel can support controller comparison;
- continuing to add small local repair variants on the same fixed public
  sources is a good next research move.

Not falsified:

- the broader self-ID RL driver hypothesis;
- the usefulness of executable-v2 scenario panels;
- the usefulness of near-miss task-quality diagnostics.

## failure_taxonomy_summary

The branch had two distinct failure modes:

```text
scenario_sampling_failure:
  M1912 produced 192 sampling failures due to road_geometry_fixed obstacle
  diagnostic deltas being mapped into env_config.obstacle.
  Status: repaired by M1914 and cleared by M1915.

zero_joint_task_quality_surface:
  M1917 found no joint clearance-containment rows across 1536 classified rows.
  Status: not a wrapper bug; this is a scenario/task-quality design blocker.
```

No actor-input contract violation, training/PPO washout, private-holdout misuse,
controller-profile tuning, or ranking leak occurred.

## public_gate_overfit_risk

The overfit risk is high if this exact branch continues. The branch repeatedly
uses the same `16` selected support-first sources and fixed public controller
profile matrix. Continuing with more local geometry or semantics tweaks would
optimize a known public zero-joint surface rather than expand the scientific
evidence.

The safe interpretation is:

```text
M1909-M1917 validates the measured-wrapper harness and exposes a task-quality
blocker; it does not justify more local repair before a broader scenario design
synthesis.
```

## next_branch_decision

Decision:

```text
stop paper_route_repair_axis_measured_wrapper
pivot to paper_route_task_quality_scenario_redesign
```

The next branch should be broader than repair-axis tweaking. It should define a
scenario-quality redesign protocol with at least:

- a positive-support feasibility ladder, so some rows can achieve joint
  clearance-containment before ranking is allowed;
- boundary and near-miss strata, so the task still contains hard handling-limit
  cases;
- fresh source sampling rather than only the current 16-source public panel;
- explicit holdout policy before controller comparison;
- a pass/fail gate that blocks ranking until joint clearance-containment support
  exists across roles/surfaces.

Next milestone:

```text
m1919-executable-v2-task-quality-scenario-redesign-plan
```

M1919 should design the new branch without running rollout, training, PPO, or
controller ranking.
