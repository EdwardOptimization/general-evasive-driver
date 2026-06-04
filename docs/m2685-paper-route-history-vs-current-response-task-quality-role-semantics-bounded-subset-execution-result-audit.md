# M2685 Paper Route History Vs Current Response Task Quality Role Semantics Bounded Subset Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2684_route_to_bounded_subset_branch_synthesis`
- manifest: `experiments/manifests/m2685-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-result-audit.json`
- audit artifact: `docs/m2685-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-result-audit.md`
- parent doc: `docs/m2684-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-preflight.md`
- parent summary: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/summary.json`
- governing plans: `docs/post-m2470-route-plan.md`, `docs/self-id-go-no-go-paper-route-plan.md`, and `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2686-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-branch-synthesis.json`
- next: `m2686-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-branch-synthesis`

## Audit Summary

M2685 accepts M2684 as a complete and claim-safe bounded subset execution
preflight. M2684 executed the M2682 proposed measured subset, preserved the
M2673 runtime-control mapping, kept role semantics analysis-only, and wrote all
required evidence artifacts.

Accepted M2684 state:

```text
status_pass: true
result_class: paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight_pass
episode rows: 216/216
accounted cells: 216/216
failure rows: 0
profiles covered: 12/12
subset specs covered: 18/18
candidate aggregates: 9
source-edge aggregates: 9
role-semantics aggregate groups: 2
runtime joins: 12/12 pass
claim-boundary rows: 37
gate rows: 30
gate_matrix_pass: true
subset expanded to full public matrix: false
```

M2684 is new closed-loop data, but it is not paper evidence or driver
performance evidence by itself. The bounded subset remains dominated by
off-track noncompletion and therefore cannot support controller-family ranking,
finite-window-vs-GRU interpretation, current-response sufficiency,
current-sim verdict, full ideal driver completion, or level3
self-identification.

## Artifact Audit

M2684 wrote the required artifacts:

```text
summary.json: present
subset_rollout_execution_summary.json: present
episode_rows.csv: 216 rows
profile_aggregate.csv: 12 rows
spec_aggregate.csv: 18 rows
candidate_aggregate.csv: 9 rows
source_edge_aggregate.csv: 9 rows
role_semantics_aggregate.csv: 2 rows
outcome_aggregate.csv: 3 rows
termination_reason_aggregate.csv: 3 rows
runtime_enforcement_join_rows.csv: 12 rows
claim_boundary_rows.csv: 37 rows
gate_matrix.csv: 30 rows
failure_rows.csv: 0 rows
run_state.json: present
doc: present
```

All 30 gate rows pass. The gate matrix verifies source lineage, M2682 subset
integrity, actor/action boundary preservation, runtime join coverage, selected
metric finiteness, role semantics actor-invisibility, absence of training/PPO/
replay/private holdout/profile-specific tuning, and required artifact
presence.

The claim boundary is clean:

```text
allowed claims: 17/17 pass
blocked claims: 20/20 not made
```

## Subset Boundary Audit

M2684 stayed inside the M2682 bounded subset:

```text
full public matrix rows: 864
M2682 subset rows: 216
M2684 executed rows: 216
unique workload rows: 216
unique specs: 18
profiles: 12
candidate groups: 9
task families: 2
expanded to full public matrix: false
```

No failed subset cell was dropped silently. The failure table is present and
empty because no rollout cell failed.

## Runtime And Actor Contract Audit

M2684 preserves the Route B runtime controls:

```text
runtime join rows: 12/12 pass
required protocol controller families mapped: 9/9
current-tiled L2 runtime profile count: 4
current-tiled runtime observed: true
L3 reset/truncated runtime profile count: 1
L3 reset/truncated policy routing ok: true
actor contract: P0 observation shape 72, action shape 3
hidden/oracle actor input detected: false
private holdout used: false
training/PPO/replay used: false
profile-specific tuning: false
```

Role semantics remain analysis-only metadata:

```text
role_semantics_actor_visible: false
hidden_oracle_actor_input_required: false
actor_input_contract_changed: false
```

## Outcome Semantics Caveat

M2684 improves the evidence state by producing new bounded closed-loop data,
but it does not solve the interpretation blocker.

Bounded subset outcomes:

| bucket | rows | share |
| --- | ---: | ---: |
| off_track_noncollision_noncompletion | 202 | 0.9352 |
| success_obstacle_pass | 11 | 0.0509 |
| collision_failure | 3 | 0.0139 |

Bounded subset terminations:

| termination reason | rows | share |
| --- | ---: | ---: |
| off_track | 203 | 0.9398 |
| none/success | 11 | 0.0509 |
| obstacle_collision | 2 | 0.0093 |

The profile rows remain diagnostic only. For example, the L3 reset/truncated
control row has 7/18 successes, L0 has 2/18, L1 has 1/18, L3 online GRU has
1/18, and all L2 finite-window/current-tiled rows have 0/18 successes on this
subset. These are not rankings or paper results because the subset is bounded,
off-track dominated, and selected from a repair-admission panel.

## Failure Taxonomy

- `contract_violation`: not observed. Actor/action shape, no hidden/oracle
  actor input, role semantics actor-invisibility, and no private holdout remain
  preserved.
- `lineage_invalid`: not observed. M2684 consumes M2682, M2673, M1690, and
  M1674 artifacts, and M2685 is pre-registered.
- `metric_artifact`: controlled for artifact completeness. Selected metrics are
  finite, but aggregate metrics remain diagnostic only.
- `scenario_sampling_failure`: active for interpretation. The bounded subset is
  still dominated by off-track noncompletion.
- `behavior_regression`: not decided. M2685 does not rank profiles or select a
  winner.
- `objective_overfit`: reduced by avoiding another 864-row full-matrix repeat,
  but still active if the branch continues with more narrow public repairs.
- `proof_washout`: controlled by the claim boundary. Success and role metrics
  remain non-verdict.

## Next Route Decision

Decision:

```text
accept_m2684_route_to_bounded_subset_branch_synthesis
```

M2684 is complete enough to audit as a dataset, but not interpretable enough to
continue directly into ranking or another narrow repair/execution loop. M2686
must synthesize the M2680-M2685 task-quality/role-semantics branch and decide
whether to continue, pivot, or stop this current-sim Route B sub-branch.

M2686 must answer:

```text
evidence_summary
supported_claims
falsified_claims
failure_taxonomy_summary
public_gate_overfit_risk
next_branch_decision
```

The synthesis should explicitly consider that M2684 created new bounded
closed-loop data but the main outcome blocker persisted:

```text
off-track terminations: 203/216
off-track outcomes: 202/216
paper verdict delta: no verdict
driver-performance delta: no claim
self-ID delta: no claim
```

## Claim Boundary

Allowed M2685 claim:

```text
M2684 bounded subset execution artifacts are complete, guardrail-clean, and
claim-safe enough to route to branch synthesis.
```

Rejected claims:

```text
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
comparison-delta verdict
driver performance
validation readiness or result
finite-window superiority
GRU superiority
current-response sufficiency
recurrent-belief advantage
level3 self-identification
paper verdict
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
```

M2685 did not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or verdict computation.
