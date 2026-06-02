# M2410 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Reset Evidence Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence_pass`
- manifest: `experiments/manifests/m2410-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence.py`
- output: `runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/summary.json`
- environment reset: `true`
- environment step/policy action: `false/false`
- repair execution/training/replay/PPO: `false`
- active config overwrite: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m \
  autodrift.paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence \
  --source-overlay-dir runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization \
  --source-effective-dir runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization \
  --output-dir runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence \
  --next-blocker m2411-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-result-audit
```

## Result

Summary:

```text
result_class: current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence_pass
candidate_family_count: 4
matched_family_count: 4
family_without_match_count: 0
source_effective_candidate_count: 54
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
unmatched_source_key_count: 95
environment_step_count: 0
policy_action_executed: false
active_config_overwrite_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Family reset coverage:

```text
c01_geometry_timing_containment:
  matched effective candidates: 3
  source-linked scenario refs: 388
  unique reset targets: 290
  unmatched source keys: 3
  family reset pass: true

c02_hidden_dynamics_response_containment:
  matched effective candidates: 24
  source-linked scenario refs: 593
  unique reset targets: 280
  unmatched source keys: 40
  family reset pass: true

c03_general_offtrack_boundary_containment:
  matched effective candidates: 30
  source-linked scenario refs: 1456
  unique reset targets: 350
  unmatched source keys: 52
  family reset pass: true

c04_role_conditioned_containment:
  matched effective candidates: 27
  source-linked scenario refs: 1068
  unique reset targets: 300
  unmatched source keys: 0
  family reset pass: true
```

Reset target distribution:

```text
baseline_reference_pack: 70
g_h_primary_pack: 70
g_primary_pack: 70
gh_minimal_pack: 70
h_primary_pack: 70
```

## Interpretation

M2410 converts the M2406 semantic candidate-family overlays into a concrete
source-linked reset panel by joining their source row keys to the M2391
reset-valid effective-candidate scenario specs.

This closes the specific M2408 gap:

```text
M2408 proved the four overlays are structurally loadable.
M2410 proves the source-linked concrete env configs behind those families can
all load and reset.
```

The result remains reset-only. It does not prove that any offtrack containment
repair works, because no M2406 repair lever was executed and no policy action
or measured rollout ran.

The 95 unmatched source keys are expected diagnostic debt, not hidden failure.
M2406 contains 203 fine-grained repair-plan keys, while M2391 contains 54
effective-candidate source keys. The unmatched rows mean M2410 supports only
the source-linked executable subset and must not be used to claim that all
repair semantics are executable.

## Claim Boundary

Supported:

```text
All four M2406 offtrack containment families have non-empty source links to
M2391 effective candidates.

The source-linked concrete reset panel contains 350 unique env configs and all
350 reset successfully.

The reset panel preserves the P0 human-view no-wheel no-oracle actor contract
and does not step environments or execute policy actions.
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

## Validation

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence.py

2 passed
```

Compile check:

```text
python -m compileall -q src tests
```

## Next

Next milestone:

```text
m2411-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-reset-evidence-result-audit
```

M2411 should audit whether M2410 is enough to admit a bounded non-ranking
measured-validation design over the source-linked reset panel. It must not rerun
reset, execute repair, train, rank families, select a winner, or make
current-sim/paper/self-ID/FW-vs-GRU verdict claims.
