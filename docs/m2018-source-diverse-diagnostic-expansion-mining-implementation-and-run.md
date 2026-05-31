# M2018 Source-Diverse Diagnostic Expansion Mining Implementation And Run

- status: completed
- decision: `source_diverse_diagnostic_expansion_mining_pass_route_to_result_audit`
- result class: `source_diverse_diagnostic_expansion_mining_pass`
- implementation: `src/autodrift/source_diverse_diagnostic_expansion_mining.py`
- focused tests: `3 passed`
- compileall: `passed`
- summary: `runs/m2018_source_diverse_diagnostic_expansion_mining/summary.json`
- source localization: `runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2`
- source measured execution: `runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat`
- environment reset/rollout in M2018: `false`
- policy action execution in M2018: `false`
- measured rollout in M2018: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_source_diverse_diagnostic_expansion_mining.py
```

Result:

```text
3 passed
```

No-rerun mining:

```bash
PYTHONPATH=src python -m autodrift.source_diverse_diagnostic_expansion_mining \
  --l2-diagnostic runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/l2_zero_success_diagnostic.csv \
  --episode-rows runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv \
  --output-dir runs/m2018_source_diverse_diagnostic_expansion_mining \
  --next-blocker m2019-source-diverse-diagnostic-expansion-mining-result-audit
```

Return code:

```text
0
```

## Pass Gate Result

M2018 passes:

```text
result_class: source_diverse_diagnostic_expansion_mining_pass
diagnostic_row_count: 88
episode_row_count: 960
candidate_count: 7
admitted_candidate_count: 6
beyond_m2016_admitted_candidate_count: 5
guardrail_violation_count: 0
```

No environment or actor execution occurred:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Expansion Candidates

Admitted candidate keys:

```text
success_stabilizer|drift_required_recovery|tier_c_boundary_near_miss|post_friction_step|drift_required
success_stabilizer|drift_required_recovery|tier_e_mitigation_only|steady_surface|drift_required
success_stabilizer|stable_aeb|tier_c_boundary_near_miss|post_friction_step|aeb_feasible
success_stabilizer|stable_aeb|tier_e_mitigation_only|post_friction_step|aeb_feasible
success_stabilizer|stable_aes_only|tier_b_feasible_emergency|post_friction_step|aes_feasible
success_stabilizer|unavoidable_mitigation|tier_b_feasible_emergency|post_friction_step|unavoidable
```

The rejected candidate is:

```text
success_stabilizer|stable_aeb|tier_c_boundary_near_miss|steady_surface|aeb_feasible
```

with:

```text
non_l2_success_count_below_threshold
non_l2_success_profile_group_count_below_threshold
```

## Diversity Boundary

M2018 expands beyond the M2016 singleton, but not into full source-kind
diversity:

```text
repair_source_kind_count: 1
role_count: 4
tier_count: 3
surface_count: 2
label_count: 4
max_candidate_source_count: 5
m2016_singleton_included: true
```

Allowed interpretation:

```text
Existing artifacts contain multiple admitted L2-zero/non-L2-success diagnostic
slices beyond the M2016 singleton across roles, tiers, surfaces, labels, and
candidate sources.
```

Forbidden interpretation:

```text
The evidence is source-kind-diverse.
The evidence ranks controller families.
The evidence proves finite-window-vs-GRU.
The evidence proves level3 self-identification.
```

## Next

Next milestone:

```text
m2019-source-diverse-diagnostic-expansion-mining-result-audit
```

M2019 should audit whether this expansion is sufficient for a bounded
multi-slice diagnostic comparison design, or whether the lack of source-kind
diversity requires task-quality support repair or scenario redesign first.
