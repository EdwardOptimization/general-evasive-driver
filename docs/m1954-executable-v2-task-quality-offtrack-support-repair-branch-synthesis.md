# M1954 Executable V2 Task-Quality Offtrack Support Repair Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- completed branch: `paper_route_task_quality_offtrack_support_repair`
- next branch: `paper_route_task_quality_calibrated_materialization`
- decision: `task_quality_offtrack_support_repair_branch_synthesis_promote_to_calibrated_materialization`
- reset/rollout/measured execution in M1954: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M1944-M1953 repaired the offtrack-dominated task-quality branch at the
source-mining layer. The branch did not run reset validation, measured
execution, replay, training, PPO, or controller ranking.

Branch progression:

```text
M1944: designed a 160-row offtrack-support repair template wave
M1945: implemented deterministic repair templates
M1946: designed no-rollout source-mining adapter
M1947: implemented adapter; broad support passed but anchor support failed 0/64
M1948: audited failure as stable-AEB anchor fallback geometry, not broad redesign
M1949: designed label-preserving anchor fallback calibration
M1950: implemented calibration; 64/64 anchors supported in calibration context
M1951: designed artifact-provenanced calibrated source-mining application
M1952: implemented calibrated source mining; full source-mining gate passed
M1953: audited M1952 and routed to synthesis before execution
```

Material evidence changed:

```text
before M1944:
  M1938 measured execution was complete but low-support/offtrack-dominated.
  M1942 found 0 comparison-ready slices and only 2 candidate-support slices.

after M1953:
  the branch has a calibrated 160-row no-rollout source-mining pass,
  source-kind gates pass,
  the old stable-AEB anchor blocker is repaired,
  and the result is ready for calibrated materialization/reset planning.
```

Key result:

```text
M1947 source mining:
  result_class: incomplete_or_fail
  supported_source_count: 66
  accepted_cell_count_total: 1949
  anchor_neighborhood: 0 / 64
  public_gate_supported_source_count: 40
  guardrail_violation_count: 0

M1952 calibrated source mining:
  result_class: pass
  supported_source_count: 130
  accepted_cell_count_total: 5981
  anchor_neighborhood: 64 / 64
  public_gate_supported_source_count: 40
  guardrail_violation_count: 0
```

Non-anchor support was preserved:

```text
success_stabilizer:        39 / 48 -> 39 / 48
offtrack_boundary_relief:  11 / 32 -> 11 / 32
mitigation_isolation_check: 16 / 16 -> 16 / 16
```

## Supported Claims

Supported task-quality/source claims:

- M1945 produced a deterministic 160-row repair template artifact;
- M1947 implemented a no-rollout source-mining adapter with complete artifacts;
- M1948 localized the failure to stable-AEB anchor fallback geometry;
- M1950 produced a label-correct calibrated fallback artifact for both
  `post_friction_step` and `steady_surface`;
- M1952 applied the calibrated artifact through provenance-tracked adapter
  input, not hard-coded geometry;
- the full calibrated no-rollout source-mining gate passes with guardrail `0`;
- the branch is ready to design calibrated materialization/reset validation.

Supported process claims:

- the harness correctly stopped threshold weakening;
- the branch preserved source label semantics rather than accepting
  `aes_feasible` rows as stable-AEB anchors;
- local-search risk was controlled by an audit and synthesis route.

## Falsified Or Unsupported Claims

Falsified:

```text
The M1946 stable-AEB anchor fallback default is sufficient.
```

Reason: M1947 classified all `64` anchor rows as `aes_feasible` and rejected
them for `stable_aeb`.

Falsified:

```text
The M1947 failure requires broad scenario redesign immediately.
```

Reason: M1950/M1952 repaired the failure with a narrow label-preserving
fallback calibration while preserving non-anchor support.

Still unsupported:

- reset validity for the calibrated repaired source set;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- high-fidelity validation readiness.

## Failure Taxonomy Summary

Primary failure type encountered:

```text
scenario_sampling_failure
```

More specifically:

```text
stable-AEB anchor fallback geometry was too hard and mapped to AES.
```

Resolution:

```text
artifact-provenanced geometry calibration:
  obstacle_distance: 52.0
  obstacle_half_width: 0.75
  speed_ref: 18.0
  mu: 0.40
```

Not observed in this branch:

```text
contract_violation
metric_artifact
private_holdout_contamination
training_instability
proof_washout
controller ranking evidence
level3 self-ID evidence
```

## Public Gate Overfit Risk

Current risk: `medium`.

Risk reducers:

- source repair used deterministic templates and explicit artifacts;
- M1950 generated calibrated fallback from a bounded classifier sweep;
- M1952 consumed the calibration artifact instead of hard-coding constants;
- the repaired source-mining pass preserved non-anchor support;
- no private holdout was used;
- no controller-specific tuning occurred.

Remaining risks:

- all source-mining evidence is still public diagnostic;
- source labels are classifier/source-quality evidence, not closed-loop success;
- the calibrated fallback repairs source support, but reset and measured
  outcomes may still fail;
- materialization must avoid selecting only easy stable-AEB anchors and losing
  the original multi-role task-quality intent.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

New branch:

```text
paper_route_task_quality_calibrated_materialization
```

Next milestone:

```text
m1955-executable-v2-task-quality-calibrated-source-materialization-design
```

M1955 should design a calibrated source materialization subset from the M1952
source rows. It should preserve source-kind diversity, role/surface diversity,
and the calibrated-anchor provenance while keeping reset, rollout, measured
execution, ranking, paper-level, and level3 self-ID claims blocked.

No reset/materialized execution is admitted until M1955 designs the exact
selection target and follow-up preflight route.
