# M2239 Paper-Route Current-Sim Task/Curriculum Readiness Diagnosis Result Audit

- status: completed
- decision: `current_sim_readiness_diagnosis_route_to_training_stability_repair_design`
- manifest: `experiments/manifests/m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit.json`
- parent result: `runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/summary.json`

## Audit Result

M2238 is a clean artifact-only diagnosis result:

```text
result_class: current_sim_task_curriculum_readiness_diagnosis_pass
missing_artifact_count: 0
row_diagnosis_count: 30
seed_diagnosis_count: 6
budget_delta_count: 15
training_plateau_row_count: 30
```

The guardrails are clean:

```text
training_started: false
rollout_started: false
environment_reset_started: false
ppo_started: false
ranking_admissible: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Route Evidence

The route-level readiness blocker remains:

```text
profile_floor_pass_count short_v0: 0
profile_floor_pass_count medium_v1: 0
unchanged_fail profile/seed rows: 11/15
unchanged_pass profile/seed rows: 4/15
fail_to_pass rows: 0
pass_to_fail rows: 0
```

This is not a near-floor calibration result:

```text
medium_fail_count: 11
medium_near_floor_count: 0
medium_return_fail_count: 11
medium_termination_fail_count: 11
```

It is also not mainly a single seed artifact:

```text
medium seed 222601 passing rows: 2/5
medium seed 222602 passing rows: 0/5
medium seed 222603 passing rows: 2/5
medium_seed_pass_range: 2
```

The budget increase contains a useful local signal but no readiness transition:

```text
return improved: 10/15
termination improved: 10/15
fail_to_pass: 0/15
```

The strongest route signal is late regression:

```text
late_regression_row_count: 18/30
training_plateau_ratio: 0.6
primary route: training_plateau_or_late_regression
secondary route: task_curriculum_repair
```

## Interpretation

The safest interpretation is:

```text
Current-sim matched-budget training is not comparison-ready, and the next
problem is not simply "more steps".
```

M2238 shows that longer training can improve some eval means, but the final
checkpoint still fails the `2/3` readiness floor and many train traces regress
after earlier better rollout windows. Therefore the next route should first
address training stability and checkpoint selection before changing the paper
comparison question.

The secondary task/curriculum signal remains real, but it should be handled
through a structured repair design rather than an immediate new training run.

## Decision

Route to training-stability repair design:

```text
m2240-paper-route-current-sim-training-stability-repair-design
```

M2240 should design, without running training:

- periodic eval/checkpoint retention or best-checkpoint selection;
- early-stop or no-regression retention policy;
- unchanged actor input contract and unchanged five-profile/three-seed panel;
- readiness-floor and guardrail checks before any future execution;
- a fallback path to task/curriculum/reward repair if checkpoint-selection
  design is insufficient.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution from M2230/M2234/M2238
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another blind budget escalation
```

## Next

Pre-register:

```text
m2240-paper-route-current-sim-training-stability-repair-design
```
