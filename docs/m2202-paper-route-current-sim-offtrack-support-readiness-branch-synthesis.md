# M2202 Paper-Route Current-Sim Offtrack-Support Readiness Branch Synthesis

- status: completed
- decision: `current_sim_offtrack_support_readiness_synthesis_continue_to_measured_execution_command_design`
- manifest: `experiments/manifests/m2202-paper-route-current-sim-offtrack-support-readiness-branch-synthesis.json`
- synthesis window: `M2192-M2201`
- next manifest: `experiments/manifests/m2203-paper-route-current-sim-offtrack-support-measured-execution-command-design.json`
- implementation in M2202: `false`
- reset in M2202: `false`
- measured execution in M2202: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2192 audited the M2190 candidate artifact as structurally clean:

```text
candidate_count: 288
duplicate_candidate_id_count: 0
boolean_guardrail_violation_count: 0
profile_specific_candidate_count: 0
actor_input_contract_change_count: 0
```

M2194 materialized the repaired candidates without rollout:

```text
repaired_executable_spec_count: 288
planned_workload_row_count: 2304
materialization_failure_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

M2197 then reset-validated the repaired executable specs:

```text
reset_attempt_count: 288
reset_success_count: 288
reset_failure_count: 0
observation_dimension_failure_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

M2200 joined the reset-valid repaired workload with profile checkpoints:

```text
materialized_workload_count: 2304
checkpoint_path_exists_count: 2304
checkpoint_path_missing_count: 0
profile_count: 8
rows_per_profile_pass: true
reset_control_alias_pass: true
profile_shortcut_violation_count: 0
profile_specific_tuning_count: 0
claim_violation_count: 0
guardrail_violation_count: 0
```

M2201 audited that readiness result as clean and identified the branch-cadence
boundary.

## Supported Claims

The branch now supports these limited claims:

```text
1. The 288-candidate offtrack-support repair artifact is structurally clean.
2. The repaired candidates have been materialized into 288 executable specs and
   2304 workload rows without actor-input contract violations.
3. All 288 repaired specs reset successfully with 72-dimensional observations.
4. The repaired workload is checkpoint-complete across 8 controller profiles.
5. The L3 reset-control alias uses the same checkpoint as L3 online GRU while
   preserving the reset/truncation control role.
```

These are task-quality readiness and workflow claims. They are not controller
performance claims.

## Falsified Claims

The branch still rejects these claims:

```text
1. The repaired panel has produced measured outcomes.
2. The repaired panel can rank L0/L1/L2/L3 controller families.
3. The finite-window vs GRU question has a verdict.
4. The branch provides paper-level benchmark evidence.
5. The branch provides level3 self-identification evidence.
```

The earlier offtrack-dominated measured panels remain the reason this repaired
panel exists. The new panel must be measured before any comparison can be
reopened.

## Failure Taxonomy Summary

The original branch failure class remains:

```text
scenario_sampling_failure
```

Reason: earlier measured current-sim panels were execution-complete but
offtrack-dominated and not comparison-ready.

The M2192-M2201 branch did not add a new scientific failure. It converted the
repair artifact into reset-valid, checkpoint-complete measured-execution
readiness. The unresolved risk is whether measured execution will still produce
low support or degenerate repeat variation.

## Public-Gate Overfit Risk

Risk is `medium`.

The repaired panel is derived from public measured failures, so it is legitimate
for repairing task quality but not for final paper claims by itself. The next
measured run should be treated as public-gate evidence. If it becomes
comparison-ready, the project must still preserve private/holdout discipline
before paper-level claims.

## Actual Capability Change

The branch changed the project capability from:

```text
deterministic support-repair candidate artifact
```

to:

```text
reset-valid and checkpoint-complete 2304-row repaired measured workload
```

This is enough to design a measured-execution command. It is not enough to rank
controllers.

## Next Branch Decision

Decision: `continue`.

The branch should continue to measured-execution command design, then only if
that design is complete:

```text
M2203 measured-execution command design
  -> measured execution implementation/run
  -> result audit
  -> outcome support and seed-diversity audit
  -> only then consider controller-family comparison or paper-route verdict
```

Hard blocks remain:

```text
no controller ranking
no winner selection
no finite-window vs GRU verdict
no paper-level benchmark evidence
no level3 self-identification claim
```

Stop or pivot if the repaired measured execution remains offtrack-dominated,
if repeat/seed diversity remains degenerate, or if the result cannot provide
balanced outcome support for the controller-family matrix.
