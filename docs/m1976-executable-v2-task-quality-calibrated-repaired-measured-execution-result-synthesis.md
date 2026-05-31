# M1976 Executable V2 Task-Quality Calibrated Repaired Measured Execution Result Synthesis

- status: completed
- synthesis decision: `pivot`
- completed branch segment: `paper_route_task_quality_calibrated_materialization`
- next branch: `paper_route_task_quality_calibrated_repaired_outcome_localization`
- decision: `task_quality_calibrated_repaired_measured_execution_synthesis_pivot_to_calibrated_outcome_localization`
- reset/rollout/measured execution in M1976: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M1966-M1975 resolved a concrete metadata blocker in the calibrated measured
execution path, then produced a complete repaired 960-row public diagnostic
measured execution. The branch did not train, replay, run PPO, tune controller
profiles, promote a checkpoint, or make ranking/paper/self-ID claims.

Branch progression:

```text
M1966: attempted calibrated measured execution and failed closed before rollout
M1967: audited the failure as offtrack parent-tier metadata normalization gap
M1968: designed explicit offtrack parent-tier sentinel semantics
M1969: implemented sentinel and reran no-reset materialization successfully
M1970: audited repaired no-reset artifacts as clean
M1971: froze repaired reset-validation command
M1972: reset-validated repaired 80-spec panel, 80/80 success
M1973: audited reset pass and admitted measured command design
M1974: froze repaired measured execution command
M1975: ran repaired measured execution, 960 rows, zero runner failures
```

Material capability changed:

```text
before M1966:
  calibrated source selection, materialization, reset validation, and runner
  implementation existed, but the first measured execution attempt had not
  yet been tested over the calibrated panel.

after M1975:
  the repaired calibrated panel has reset-valid executable specs, a
  metadata-preserving measured runner, complete 960-row measured artifacts,
  and a documented low-support outcome blocker.
```

M1966 failure evidence:

```text
episode_count: 0
environment_rollout_started: false
measured_rollout_started: false
guardrail_violation_count: 0
validation failure: missing_spec_field=parent_feasibility_tier_id
affected source slice: offtrack_boundary_relief
affected task sources: 8
affected workload cells: 96
```

M1969 repair evidence:

```text
result_class: task_quality_calibrated_materialization_preflight_pass
executable_task_spec_count: 80
planned_workload_cell_count: 960
parent_feasibility_tier_blank_spec_count: 0
parent_feasibility_tier_blank_workload_count: 0
parent_feasibility_tier_normalized_spec_count: 8
parent_feasibility_tier_normalized_workload_count: 96
offtrack_parent_tier_sentinel: tier_not_applicable_offtrack_boundary_relief
guardrail_violation_count: 0
```

M1972 reset evidence:

```text
result_class: task_quality_calibrated_reset_validation_preflight_pass
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

M1975 measured execution evidence:

```text
result_class: task_quality_calibrated_measured_execution_pass
episode_count: 960
spec_count: 80
profile_count: 12
failure_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
environment_rollout_started: true
policy_action_executed: true
measured_rollout_started: true
training_started: false
replay_started: false
ppo_used: false
promoted: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

M1975 raw outcomes:

```text
success_obstacle_pass: 38 / 960 = 3.96%
collision_failure: 150 / 960 = 15.63%
off_track_noncollision_noncompletion: 772 / 960 = 80.42%
```

Source-kind outcome support:

```text
anchor_neighborhood:
  episodes: 384
  success_rate: 0.0000
  collision_rate: 0.0000

mitigation_isolation_check:
  episodes: 192
  success_rate: 0.0677
  collision_rate: 0.5521

offtrack_boundary_relief:
  episodes: 96
  success_rate: 0.0000
  collision_rate: 0.0000

success_stabilizer:
  episodes: 288
  success_rate: 0.0868
  collision_rate: 0.1528
```

## Supported Claims

Supported task-quality claims:

- the M1966 measured execution failure was a metadata normalization blocker,
  not a simulator rollout, policy, training, or actor-contract failure;
- the explicit sentinel `tier_not_applicable_offtrack_boundary_relief`
  repaired the offtrack-boundary-relief parent-tier metadata gap without
  relaxing runner validation;
- the repaired 80-spec calibrated panel reset-validates cleanly under the
  strict human-view observation contract;
- the repaired calibrated measured runner can execute the full
  `80 x 12 = 960` public diagnostic workload with complete metrics and clean
  guardrails;
- M1975 preserved repair-source metadata into episode and aggregate artifacts;
- the branch produced complete public diagnostic measured data for the repaired
  calibrated panel.

Supported process claims:

- the workflow synthesis guard correctly prevents another narrow local repair
  before branch-level interpretation;
- M1966 failed closed and preserved failure artifacts instead of silently
  dropping malformed rows;
- repair was staged through no-reset materialization, reset validation, command
  design, measured execution, and synthesis;
- no private holdout, controller-specific tuning, actor input change, training,
  replay, PPO, promotion, or ranking was used.

## Falsified Or Unsupported Claims

Falsified in this branch:

```text
The M1958/M1960 calibrated materialization artifacts were immediately ready
for measured execution without additional repair.
```

Reason: M1966 found blank `parent_feasibility_tier_id` values in the selected
offtrack-boundary-relief slice. The runner correctly rejected those rows before
rollout.

Falsified for current branch readiness:

```text
The repaired calibrated measured result is directly comparison-ready.
```

Reason: M1975 completed execution, but success support is only `38/960` and
the outcome distribution remains dominated by offtrack noncompletion
(`772/960`). Ranking from this public diagnostic surface would mostly measure
task/outcome support artifacts, not controller-family quality.

Still unsupported:

- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU conclusion;
- policy improvement;
- level3 self-identification;
- high-fidelity validation readiness.

## Failure Taxonomy Summary

Observed failures/blockers:

```text
M1966: scenario_sampling_failure / metadata_normalization_gap
M1975: outcome_support_low_offtrack_dominated
```

Resolved:

```text
metadata_normalization_gap:
  resolved by explicit offtrack parent-tier sentinel and repaired materialization
```

Still active:

```text
outcome_support_low_offtrack_dominated:
  M1975 has complete measured data but too little success support for ranking
```

Not observed in this branch:

```text
contract_violation
metric_artifact
private_holdout_contamination
training_instability
proof_washout
behavior_regression
controller ranking evidence
level3 self-ID evidence
```

## Public Gate Overfit Risk

Current risk: `medium_high`.

Risk reducers:

- the repaired panel is source-diverse across repair source kinds, roles,
  normalized surfaces, sampled labels, and controller profiles;
- M1975 ran the frozen command from M1974 without profile-specific tuning;
- guardrails explicitly block ranking, paper-level, and level3 claims;
- M1966 negative result and M1975 low-support result are both recorded.

Remaining risks:

- all evidence is public diagnostic evidence, not private holdout evidence;
- the panel has only `38` successful obstacle passes;
- offtrack noncompletion is broad enough that direct profile ranking would
  overfit to support distribution;
- the M1975 schema differs from the older M1942 localization schema because
  it carries repair provenance and `parent_*` fields, so the old localizer
  should not be blindly reused as if it were schema-exact.

## Next Branch Decision

Decision:

```text
pivot
```

New branch:

```text
paper_route_task_quality_calibrated_repaired_outcome_localization
```

Next milestone:

```text
m1977-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-implementation-and-run
```

M1977 should implement and run a no-rerun calibrated-repaired outcome
localizer over M1975 artifacts. It should preserve M1975 repair provenance and
map the calibrated schema explicitly:

```text
tier dimension: parent_feasibility_tier_id
surface dimension: normalized_surface_variant and parent_surface_variant
repair dimensions: repair_source_kind, selection_quota_name, base_geometry_source
standard dimensions: profile_name, source_role_semantics, sampled_obstacle_label
```

The localizer should answer:

- where the `38` successes are concentrated;
- whether offtrack dominance is tied to repair source kind, role, surface,
  profile, label, or base geometry;
- whether any calibrated-repaired slice is comparison-ready;
- whether offtrack-boundary-relief rows are now merely diagnostic or still a
  task-quality blocker;
- whether the correct next branch is task-quality repair, comparison design,
  scenario redesign, or support collection.

No new reset, rollout, measured execution, ranking, paper-level claim, or
level3 self-ID claim is admitted by this synthesis.
