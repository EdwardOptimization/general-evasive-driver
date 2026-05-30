# M1852 Executable V2 Support-First Source Mining Implementation

- status: completed
- decision: `support_first_source_mining_implementation_pass_route_to_candidate_template_design`
- branch: `paper_route_executable_v2_support_first_source_mining`
- parent design: `docs/m1851-executable-v2-support-first-source-mining-design.md`
- source mining run on project artifacts: `false`
- materialized executable-v2 rows generated: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Implementation

M1852 adds a no-reset helper:

```text
src/autodrift/executable_v2_support_first_source_mining.py
```

and focused tests:

```text
tests/test_executable_v2_support_first_source_mining.py
```

The helper accepts candidate source/profile rows from CSV or JSON, scans the
specified obstacle-distance and obstacle-half-width grid with the existing
`classify_obstacle_scenario` model, applies role-specific support criteria, and
writes metadata-gate-compatible support evidence.

It does not reset the environment, execute policy actions, run measured
rollouts, train, replay, run PPO, or generate materialized executable-v2 rows.

## Implemented Outputs

The helper writes:

```text
summary.json
support_first_source_candidates.csv
support_first_profile_support.csv
support_first_accepted_cells.csv
support_first_blocked_candidates.csv
support_first_role_summary.csv
support_first_materialization_admissibility_input.csv
support_first_claim_boundary.csv
```

`support_first_materialization_admissibility_input.csv` carries the M1846
contract fields, including:

```text
support_contract_id
source_role_semantics
source_required_label
source_allowed_labels
source_support_status
source_support_evidence_artifact
source_support_evidence_stage
source_support_profile_count
source_support_feasible_profile_count
source_support_accepted_cell_count_total
source_support_label_counts
source_support_reject_reason_counts
source_support_failure_reason
materialization_admissible
materialization_block_reason
claim_boundary_context
```

## Role Coverage

Focused tests cover:

- `stable_aes_only`: accepted AES cells with `require_aeb_infeasible=true`;
- `stable_aeb`: AEB cells do not certify AES but do certify AEB;
- `drift_required_recovery`: drift-required cells are separate from stable AES;
- `unavoidable_mitigation`: unavoidable cells require a mitigation metric
  contract;
- multi-profile stable roles require all profiles in a source to be supported;
- claim boundaries block materialization, ranking, and paper-level claims.

## Verification

Focused:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest tests/test_executable_v2_support_first_source_mining.py -q
```

Result:

```text
7 passed in 0.08s
```

Full:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1763 passed, 4 warnings in 9.05s
```

## Route Adjustment

M1851 expected implementation to route directly to source-mining execution
design. After implementation, the cleaner route is one intermediate design:

```text
m1853-executable-v2-support-first-candidate-template-design
```

Reason: the helper intentionally requires explicit candidate source/profile
rows. Before a project-artifact run, the candidate template must be fixed with
role, grid, speed, friction, diversity, and claim-boundary rules. This avoids
smuggling source-selection choices into an execution milestone.

## Guardrails

- project artifact source mining run: `false`
- project artifact scan: `false`
- materialized executable-v2 rows generated: `false`
- source repair payload generated: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
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

- support-first source mining helper implementation;
- focused and full tests passed;
- candidate-template design route.

Unsupported:

- project artifact source mining result;
- materialized executable-v2 rows;
- reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
