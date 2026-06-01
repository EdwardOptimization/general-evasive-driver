# M2262 Paper-Route Current-Sim Midcourse Corridor-Containment Training Execution

- status: completed
- decision: `current_sim_midcourse_corridor_containment_training_execution_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2262-paper-route-current-sim-midcourse-corridor-containment-training-execution.json`
- parent matrix: `runs/m2259_paper_route_current_sim_midcourse_corridor_containment_configs/training_matrix.csv`
- result artifact: `runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/summary.json`

## Execution Result

M2262 completed the fixed targeted containment training panel:

```text
result_class: current_sim_training_stability_repair_execution_pass
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
expected_candidate_count: 120
runtime_seconds: 317.98824217612855
```

The execution guardrails held:

```text
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
profile_set_matched: true
seed_set_matched: true
source_contract_violation_count: 0
source_budget_violation_count: 0
guardrail_violation_count: 0
validation_pass: true
training_started: true
ppo_started: true
policy_action_executed: true
environment_rollout_started: true
```

No ranking or paper claim is admitted:

```text
ranking_admissible_count: 0
winner_selected: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Profile Aggregates

M2262 still does not pass the pre-registered `2/3` seed readiness floor for any
profile:

```text
final_checkpoint_profile_floor_pass_count: 0
selected_checkpoint_profile_floor_pass_count: 0
```

Selected checkpoint aggregates:

| profile | selected passing seeds | selected return mean | selected termination mean | selected beats final |
| --- | ---: | ---: | ---: | ---: |
| L0_current_masked | `1/3` | `59.00982` | `0.39583` | `2/3` |
| L1_one_step | `1/3` | `58.96770` | `0.39583` | `1/3` |
| L2_window_25 | `1/3` | `61.67868` | `0.39583` | `3/3` |
| L2_window_50 | `1/3` | `62.55318` | `0.39583` | `2/3` |
| L3_online_gru | `0/3` | `51.87407` | `0.52083` | `3/3` |

Across all selected rows:

```text
selected_eval_return_mean: 58.81669
selected_eval_termination_rate_mean: 0.42083
selected_readiness_floor_pass_count: 4/15
selected_beats_final_count: 11/15
```

Compared with M2250 selected checkpoints, the targeted containment panel has
lower selected return but also slightly lower selected termination rate:

```text
M2250 selected return mean: 64.21352
M2262 selected return mean: 58.81669
M2250 selected termination mean: 0.43958
M2262 selected termination mean: 0.42083
```

This is not yet outcome evidence. The targeted repair was designed for
midcourse/mild offtrack slices, so selected checkpoint localization remains
necessary before deciding whether the repair helped.

## Classification

Primary classification:

```text
midcourse_corridor_containment_training_execution_complete_but_readiness_still_below_floor
```

Supported:

- The targeted containment config matrix is executable and guardrail clean.
- Candidate-checkpoint evidence is complete: `120` candidate rows and `15`
  selected rows.
- Termination is slightly lower than M2250 selected aggregate.

Not supported:

- The targeted repair is comparison-ready.
- A profile can be ranked or selected as a winner.
- The repair reduced midcourse mild offtrack without raising collision risk.
- Any paper-level, finite-window-vs-GRU, or level3 self-identification claim.

## Route Decision

Route to:

```text
m2263-paper-route-current-sim-midcourse-corridor-containment-training-execution-result-audit
```

M2263 should audit M2262 before any additional training. The audit must decide
whether the next route is selected-checkpoint outcome localization over the
M2262 selected checkpoints, branch synthesis, or another bounded repair.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another blind budget escalation
```

## Next

Pre-register:

```text
m2263-paper-route-current-sim-midcourse-corridor-containment-training-execution-result-audit
```
