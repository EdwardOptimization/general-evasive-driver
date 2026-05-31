# M1916 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper Rerun Result Audit

- status: completed
- decision: `measured_wrapper_rerun_result_audit_pass_route_to_outcome_localization`
- audited execution: `docs/m1915-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-execution-rerun.md`
- summary: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/summary.json`
- episode rows: `runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/episode_rows.csv`
- audit rerun/reset/rollout/measured execution: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness

M1915 is a clean execution artifact:

```text
matrix rows: 1536
planned rollout rows: 960
measured rollout rows: 960
import/postprocess rows: 576
combined panel rows: 1536
failure rows: 0
guardrail violations: 0
```

M1912's blocker is cleared:

```text
M1912 sampling failures: 192
M1915 sampling failures: 0
```

## Row Balance

Execution kind balance:

```text
rollout_geometry_variant: 960
postprocess_existing_episode: 384
import_existing_episode: 192
```

Repair-axis balance:

```text
8 repair-axis variants x 192 rows each
```

Task-quality axis balance:

```text
baseline_and_semantics_retention: 384
contained_collision_clearance_feasibility: 384
post_clearance_containment_recovery: 576
unavoidable_mitigation_semantics: 192
```

Scenario/control balance:

```text
role panels: 4 x 384 rows
role surfaces: 8 x 192 rows
controller profiles: 12 x 128 rows
base task sources: 16
```

All rows preserve the diagnostic boundary:

```text
diagnostic_only_no_ranking_claim: True for 1536/1536
private_holdout_used: False for 1536/1536
promoted: False for 1536/1536
training_started/replay_started/ppo_used: False for 1536/1536
actor_input_contract_changed: False for 1536/1536
controller_family_ranking_claim_made: False for 1536/1536
paper_level_claim_made: False for 1536/1536
level3_self_id_claim_made: False for 1536/1536
```

## Outcome Surface

The complete panel is not yet a controller-ranking result:

```text
success: 0 / 1536
collision=True: 279 / 1536
termination_reason=off_track: 1275 / 1536
outcome_bucket=off_track_noncollision_noncompletion: 1257 / 1536
outcome_bucket=collision_failure: 279 / 1536
```

The imported/postprocessed subset still shows the known clearance/containment
conflict:

```text
clearance_only_offtrack: 480
containment_collision: 90
collision_and_offtrack: 6
joint clearance+containment pass: 0
```

The `960` newly measured `rollout_geometry_variant` rows are count-complete but
are not yet uniformly postprocessed into the same clearance/containment
conflict taxonomy. Their `postprocess_primary_conflict_class` is
`other_non_success`, and the explicit `obstacle_clearance_pass` /
`road_containment_pass` fields are blank. Raw `success=False` is therefore too
coarse to decide which task-quality axis, if any, moved the scenario surface.

## Decision

M1916 passes as a result audit:

- the measured-wrapper rerun is complete and guardrail-clean;
- the M1912 sampling failure did not repeat;
- the row balance is sufficient for a no-rerun outcome localization;
- direct controller-family ranking remains blocked;
- task-quality interpretation must first classify the newly measured geometry
  rows with the same clearance/containment/near-miss taxonomy.

Supported:

- M1915 is complete enough for a bounded no-rerun outcome localization;
- no additional execution repair is needed before that localization.

Unsupported:

- task-quality repair success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1917-executable-v2-support-first-task-quality-repair-axis-measured-panel-outcome-localization
```

M1917 should compute a consistent no-rerun conflict/near-miss localization over
the full M1915 panel, especially the `960` measured geometry rows. If that still
cannot produce interpretable task-quality evidence, the branch should synthesize
instead of opening another repair loop.
