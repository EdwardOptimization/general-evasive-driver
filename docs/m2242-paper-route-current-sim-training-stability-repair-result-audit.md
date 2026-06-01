# M2242 Paper-Route Current-Sim Training-Stability Repair Result Audit

- status: completed
- decision: `current_sim_training_stability_partial_repair_route_to_selected_checkpoint_outcome_localization_design`
- manifest: `experiments/manifests/m2242-paper-route-current-sim-training-stability-repair-result-audit.json`
- parent result: `runs/m2241_paper_route_current_sim_training_stability_repair_execution/summary.json`

## Audit Result

M2241 is a clean execution artifact:

```text
result_class: current_sim_training_stability_repair_execution_pass
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
all_run_metrics_finite: true
all_candidate_metrics_finite: true
all_selected_metrics_finite: true
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

M2241 also followed the design boundary:

```text
total_steps: 32768
checkpoint_interval_steps: 4096
profile_set_matched: true
seed_set_matched: true
actor_input_contract_changed: false
private_holdout_used: false
```

## Final vs Selected Checkpoints

Checkpoint retention has real value:

```text
selected_beats_final_count: 12/15
```

The strongest example is `L3_online_gru` seed `222602`:

| item | final checkpoint | selected checkpoint |
| --- | ---: | ---: |
| step | `32768` | `12288` |
| eval_return_mean | `35.0936` | `67.1743` |
| eval_termination_rate | `0.75` | `0.28125` |
| readiness_floor_pass | `false` | `true` |

However, checkpoint retention does not solve route-level readiness:

```text
final_checkpoint_profile_floor_pass_count: 0
selected_checkpoint_profile_floor_pass_count: 0
```

Selected checkpoint profile aggregates:

| profile | selected passing seeds | selected return mean | selected termination mean |
| --- | ---: | ---: | ---: |
| L0_current_masked | `1/3` | `49.5519` | `0.40625` |
| L1_one_step | `1/3` | `49.0116` | `0.42708` |
| L2_window_25 | `1/3` | `52.0459` | `0.40625` |
| L2_window_50 | `1/3` | `52.6299` | `0.39583` |
| L3_online_gru | `1/3` | `45.9477` | `0.47917` |

No profile reaches the pre-registered `2/3` seed floor.

## Classification

Primary classification:

```text
training_stability_partial_repair_but_readiness_still_below_floor
```

Supported:

- Final-checkpoint late regression is a real issue.
- Periodic checkpoint retention should remain in future training recipes.
- Some seeds can be recovered by selecting earlier checkpoints.

Not supported:

- Checkpoint selection alone is enough to make the current panel comparison-ready.
- More checkpoint-selection local search is the right next step.
- The current result supports profile ranking, finite-window-vs-GRU, paper-level
  evidence, or self-identification claims.

## Route Decision

Route to selected-checkpoint outcome localization design:

```text
m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design
```

Reason:

```text
Selected checkpoints improved final metrics but still fail readiness broadly.
Before reward/task/curriculum repair, we need episode-level outcome evidence:
offtrack, collision, max-step noncompletion, recovery, and termination timing.
```

The next branch should keep M2241 selected checkpoints as diagnostic inputs and
design a no-training public rollout/localization panel. It must not rank
profiles; it should identify failure modes and repair targets.

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
another checkpoint-selection-only run
another blind budget escalation
```

## Next

Pre-register:

```text
m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design
```
