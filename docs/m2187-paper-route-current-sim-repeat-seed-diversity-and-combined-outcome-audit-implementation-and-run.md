# M2187 Paper-Route Current-Sim Repeat Seed-Diversity and Combined-Outcome Audit Implementation and Run

- status: completed
- decision: `current_sim_repeat_seed_diversity_combined_outcome_audit_not_comparison_ready_route_to_result_audit`
- manifest: `experiments/manifests/m2187-paper-route-current-sim-repeat-seed-diversity-and-combined-outcome-audit-implementation-and-run.json`
- summary: `runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/summary.json`
- focused tests: `2 passed`
- training in M2187: `false`
- measured execution in M2187: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Ran

M2187 implements:

```text
src/autodrift/paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit.py
tests/test_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit.py
```

No-rerun audit command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit \
  --original-output-dir runs/m2174_paper_route_current_sim_controlled_comparison_measured_execution \
  --original-workload runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv \
  --repeat-output-dir runs/m2184_paper_route_current_sim_repeat_measured_execution \
  --repeat-workload runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv \
  --output-dir runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit
```

## Result

```text
result_class: current_sim_repeat_seed_diversity_combined_outcome_audit_not_comparison_ready
combined_episode_count: 960
repeat_count: 3
repeat_counts:
  repeat_0_existing: 320
  repeat_1_seed_21761: 320
  repeat_2_seed_21762: 320
completeness_pass: true
comparison_ready: false
```

Combined outcome support:

```text
combined_success_count: 163
combined_collision_count: 56
combined_offtrack_count: 741
combined_success_rate: 0.16979166666666667
combined_collision_rate: 0.058333333333333334
combined_offtrack_rate: 0.771875
outcome_support_pass: false
```

Readiness thresholds:

```text
min_combined_success_count: 240
max_combined_offtrack_rate: 0.60
min_success_count_per_repeat: 80
per_repeat_success_min: 50
```

Seed-diversity audit:

```text
checkpoint_duplicate_count: 0
repeat_aggregate_equal: true
profile_vector_equal: true
seed_diversity_status: suspicious_identical_repeat_outcome_vectors
```

Interpretation:

```text
The repeat checkpoints are not byte-identical under the hash check, but
repeat_1 and repeat_2 produce identical aggregate and profile-level outcome
vectors. Treat this as suspicious and audit before ranking.
```

## Artifacts

```text
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/summary.json
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/combined_repeat_aggregate.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/profile_repeat_outcome_aggregate.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/checkpoint_hash_rows.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/repeat_diversity_flags.csv
runs/m2187_paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit/comparison_readiness_claim_boundary.csv
```

## Claim Boundary

Allowed claim:

```text
The combined M2174+M2184 repeat panel is execution-complete but not
comparison-ready under the registered support and seed-diversity gates.
```

Still blocked:

```text
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2188 must audit the no-rerun audit result and decide whether to route to
task-quality/offtrack repair, repeat seed-diversity repair, or another
comparison-readiness step. No ranking is allowed before M2188.
