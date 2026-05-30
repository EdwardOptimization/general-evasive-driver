# M1803 Executable V2 Stable Source-Label Top-Up Preflight Implementation

- status: completed
- decision: `stable_source_label_topup_preflight_implementation_pass_route_to_execution_design`
- module: `src/autodrift/executable_v2_stable_source_label_topup_preflight.py`
- test: `tests/test_executable_v2_stable_source_label_topup_preflight.py`
- focused test command: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest tests/test_executable_v2_stable_source_label_topup_preflight.py -q`
- focused test result: `2 passed in 0.06s`
- project artifact execution: `false`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Summary

M1803 implements the no-reset stable source-label top-up planner designed in
M1802. It reads replacement needs, source-label support rows, and stable source
metadata, then writes target/candidate/materialization planning artifacts
without running reset or rollout.

Candidate classes implemented:

```text
exact_existing_candidate
metadata_only_untrusted
near_existing_candidate
new_materialization_required
```

The implementation explicitly blocks metadata-only shortcuts: an exact metadata
candidate observed as `unsupported_systematic` is classified as
`metadata_only_untrusted`, is not admissible as a direct replacement, and still
requires new materialization or reset-probe evidence.

## Implemented Artifacts

The helper writes:

```text
summary.json
stable_topup_targets.csv
stable_candidate_source_pool.csv
stable_topup_candidate_rows.csv
stable_new_materialization_need_rows.csv
stable_topup_claim_boundary.csv
```

The claim boundary keeps direct measured execution and controller-family ranking
blocked.

## Focused Test Coverage

Focused tests cover:

- `exact_existing_candidate` with observed support and direct replacement
  admissibility;
- `metadata_only_untrusted` for exact metadata support with observed systematic
  failure;
- `near_existing_candidate` for label/hidden match with geometry mismatch;
- `new_materialization_required` when no direct observed replacement exists;
- empty candidate-source pool preservation;
- claim-boundary outputs;
- no label leakage and ranking blocked.

No project artifact execution occurred.

## Route Decision

Route to:

```text
m1804-executable-v2-stable-source-label-topup-execution-design
```

M1804 should fix the exact command and expected counts for running this helper
on M1800/M1771 artifacts. Execution must remain a separate milestone.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- project artifact execution: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- no-reset stable top-up planner implementation;
- focused tests for candidate classes and metadata-only guardrail.

Unsupported:

- project-artifact top-up execution result;
- repaired reset feasibility pass;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
