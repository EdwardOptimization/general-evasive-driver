# M2411 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Reset Evidence Result Audit

- status: completed
- decision: `source_linked_reset_evidence_accepted_route_to_measured_validation_design`
- manifest: `experiments/manifests/m2411-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-result-audit.json`
- parent implementation: `docs/m2410-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-implementation.md`
- parent summary: `runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/summary.json`
- rerun/reset/rollout/repair/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2411 accepts M2410 as a clean reset-only source-linked evidence artifact.

Accepted evidence:

```text
result_class: current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence_pass
candidate_family_count: 4
matched_family_count: 4
family_without_match_count: 0
matched_effective_candidate_count: 54
source_linked_scenario_reference_count: 3505
unique_reset_target_count: 350
static_validation_failure_count: 0
environment_load_attempt_count: 350
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
family_reset_pass_count: 4
family_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
active_config_overwrite_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Per-family coverage:

```text
c01_geometry_timing_containment:
  matched effective candidates: 3
  scenario refs: 388
  unique reset targets: 290
  unmatched source keys: 3

c02_hidden_dynamics_response_containment:
  matched effective candidates: 24
  scenario refs: 593
  unique reset targets: 280
  unmatched source keys: 40

c03_general_offtrack_boundary_containment:
  matched effective candidates: 30
  scenario refs: 1456
  unique reset targets: 350
  unmatched source keys: 52

c04_role_conditioned_containment:
  matched effective candidates: 27
  scenario refs: 1068
  unique reset targets: 300
  unmatched source keys: 0
```

## Boundary Checks

Reset-only boundary:

```text
environment_reset_started: true
environment_step_count: 0
policy_action_executed: false
measured_rollout_started: false
repair_execution_started: false
training_started: false
replay_started: false
ppo_used: false
```

Contract boundary:

```text
actor_input_contract_changed: false
hidden_oracle_feature_injection: false
static_validation_failure_count: 0
```

Ranking/verdict boundary:

```text
ranking_admissible_count: 0
winner_selected_count: 0
candidate_family_ranking_claim_made: false
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
training_repair_success_claim_made: false
current_sim_verdict_claim_made: false
```

## Unmatched-Key Diagnostic

M2410 reports `95` unmatched source keys:

```text
c01_geometry_timing_containment: 3
c02_hidden_dynamics_response_containment: 40
c03_general_offtrack_boundary_containment: 52
c04_role_conditioned_containment: 0
```

This does not invalidate reset evidence, because every family has non-empty
source links and every unique reset target succeeds. It does limit the claim:
the reset panel represents the M2406 families through the M2391 executable
source-linked subset, not through every fine-grained M2406 repair-plan key.

M2412 must preserve this caveat in any measured-validation design. It must not
turn unmatched-key coverage into a winner/ranking decision.

## Route Decision

Decision:

```text
source_linked_reset_evidence_accepted_route_to_measured_validation_design
```

Next milestone:

```text
m2412-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-design
```

M2412 should freeze a bounded non-ranking measured-validation design over the
M2410 reset panel. The recommended denominator is:

```text
350 unique reset targets x 15 selected checkpoints = 5250 measured episodes
```

The design should aggregate outcomes by source-linked family membership, but
must not rank families or select a winner. Each episode can belong to multiple
families; family membership is a diagnostic slice, not a mutually exclusive
ranking axis.

## Failure Taxonomy

Observed:

```text
source_linked_reset_evidence_ready: 4/4 families, 350/350 resets
unmatched_source_key_diagnostic: 95 unmatched fine-grained keys
driver_outcome_failure: offtrack-dominated failure remains inherited from M2397
```

Not observed:

```text
scenario_sampling_failure
lineage_invalid
contract_violation
metric_artifact
active config overwrite
repair execution
training repair success
candidate/profile/controller ranking
winner selection
```

## Claim Boundary

Supported:

```text
M2410 is accepted as reset-only source-linked evidence.

The next admissible route is bounded non-ranking measured-validation design.
```

Blocked:

```text
measured driver improvement
repair execution
scenario redesign executed
training repair success
candidate family ranking
support/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```
