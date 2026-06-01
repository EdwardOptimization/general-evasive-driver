# M2238 Paper-Route Current-Sim Task/Curriculum Readiness Diagnosis Implementation

- status: completed
- decision: `current_sim_task_curriculum_readiness_diagnosis_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2238-paper-route-current-sim-task-curriculum-readiness-diagnosis-implementation.json`
- command: `PYTHONPATH=src python -m autodrift.paper_route_current_sim_task_curriculum_readiness_diagnosis --output-dir runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis`
- summary: `runs/m2238_paper_route_current_sim_task_curriculum_readiness_diagnosis/summary.json`

## Outputs

M2238 implements the M2237 artifact-only diagnosis and reads only existing
M2230/M2234 training artifacts. It does not reset an environment, run rollout,
execute policy actions, train, replay, run PPO, use private holdout, rank
profiles, select a winner, or make paper/self-ID claims.

Generated artifacts:

- `row_diagnosis.csv`: `30` row-level readiness-floor diagnostics.
- `seed_diagnosis.csv`: `6` seed-level summaries.
- `budget_delta.csv`: `15` short-v0 to medium-v1 profile/seed deltas.
- `training_plateau.csv`: `30` train-metric plateau/late-regression rows.
- `claim_audit.csv`: blocked/admissible claim audit.
- `summary.json`: route classification and guardrail summary.

## Diagnosis Result

The diagnosis completed without artifact gaps:

```text
result_class: current_sim_task_curriculum_readiness_diagnosis_pass
missing_artifact_count: 0
row_diagnosis_count: 30
budget_delta_count: 15
training_plateau_row_count: 30
late_regression_row_count: 18
```

The readiness-floor state remains unchanged at the route level:

| item | short-v0 | medium-v1 |
| --- | ---: | ---: |
| profile_floor_pass_count | `0` | `0` |
| per-profile passing seeds | max `1/3` | max `1/3` |
| unchanged pass profile/seed rows | `4` | `4` |
| unchanged fail profile/seed rows | `11` | `11` |

The row-level floor reasons are:

```text
pass: 8
return_and_termination: 21
termination_only: 1
```

The medium-v1 failed rows are broad failures rather than near-threshold misses:

```text
medium_fail_count: 11
medium_near_floor_count: 0
medium_return_fail_count: 11
medium_termination_fail_count: 11
```

The short-to-medium budget increase has some local signal but no readiness
transition:

```text
improved_return_count: 10/15
improved_termination_count: 10/15
fail_to_pass_count: 0
pass_to_fail_count: 0
unchanged_fail_count: 11
unchanged_pass_count: 4
```

Seed concentration is visible but not the primary route:

```text
medium seed 222601 passing rows: 2/5
medium seed 222602 passing rows: 0/5
medium seed 222603 passing rows: 2/5
medium_seed_pass_range: 2
```

The strongest diagnosis is training plateau or late regression:

```text
training_plateau_count: 18/30
training_plateau_ratio: 0.6
```

## Route Classification

Primary route:

```text
training_plateau_or_late_regression
```

Reason:

```text
18/30 training traces show late return or termination regression; another blind
budget increase is not an admissible next step.
```

Secondary route:

```text
task_curriculum_repair
```

This means the next step should audit the diagnosis before any new training and
then decide whether to design a task/curriculum/reward/termination repair. It
should not continue by simply increasing training budget.

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

Pre-register result audit:

```text
m2239-paper-route-current-sim-task-curriculum-readiness-diagnosis-result-audit
```
