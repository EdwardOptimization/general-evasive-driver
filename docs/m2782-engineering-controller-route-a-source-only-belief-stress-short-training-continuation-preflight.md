# M2782 Engineering Controller Route A Source-Only Belief-Stress Short-Training Continuation Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight_pass`
- manifest: `experiments/manifests/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight.json`
- summary: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/summary.json`
- candidate checkpoint: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt`
- checkpoint manifest: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoint_manifest.json`
- training curriculum rows: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/training_curriculum_rows.csv`
- training run rows: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/training_run_rows.csv`
- proof gate rows: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/proof_gate_rows.csv`
- generalization gate rows: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/generalization_gate_rows.csv`
- promotion guard rows: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/promotion_guard_rows.csv`
- follow-up manifest: `experiments/manifests/m2783-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-result-audit.json`
- next: `m2783-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-result-audit`

## Result

M2782 ran one bounded source-only belief-stress short-training continuation
preflight from the M2655 source checkpoint and the audited M2779
curriculum. It wrote a candidate checkpoint for audit, not promotion.

```text
training_curriculum_rows: 18
training_run_rows: 54
proof_holdout_probe_rows: 18
proof_gate_rows: 8
generalization_gate_rows: 6
promotion_guard_rows: 4
candidate_checkpoint_written: True
checkpoint_behavior_changed: True
failed_gate_ids: none
```

## Actor And Claim Boundary

Actor input stayed at P0 observation 72 and action 3. Stress, admission,
curriculum, role, dynamics, outcome, success, progress, route, and verdict
labels remained evaluator metadata and were not actor-visible. Mitigation
reference rows stayed outside ordinary denominators.

M2782 does not validate, rank, promote, compute a success-rate verdict,
claim repair success, driver performance, paper evidence, current-sim
verdict, high-fidelity validation, full ideal driver completion, or
level3 self-identification.
