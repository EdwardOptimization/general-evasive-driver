# M1389 Paper-Route History-Profile Three-Seed Public Pilot Result Audit

## Summary

M1389 audits the M1388 three-seed fixed-budget public profile pilot.

Synthesis decision:

```text
pivot
```

Closed branch:

```text
paper_route_history_profile_comparison_protocol
```

Opened branch:

```text
paper_route_causal_history_necessity_task_design
```

M1389 performs no training, PPO, new evaluation, promotion, private holdout,
corpus export, actor-input expansion, profile-ranking claim, paper-level claim,
or self-identification claim.

## M1388 Evidence

Artifact:

```text
runs/m1388_history_profile_three_seed_public_pilot/summary.json
```

Completion:

```text
result_class: corrected_profile_pilot_completed
profile_count: 8
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
actor_input_contract_changed: false
```

M1388 is a clean public profile pilot. It is valid public trend evidence.

## Public Trend Audit

Aggregate success / collision / mean margin:

| Profile | Success | Collision | Mean Margin |
| --- | ---: | ---: | ---: |
| `L0_current_masked` | 0.52083 | 0.38542 | 0.78989 |
| `L1_one_step` | 0.47396 | 0.43229 | 0.67413 |
| `L2_window_13` | 0.56771 | 0.43229 | 0.71303 |
| `L2_window_13_current_tiled` | 0.56250 | 0.43750 | 0.70532 |
| `L2_window_25` | 0.55729 | 0.44271 | 0.70168 |
| `L2_window_25_current_tiled` | 0.56250 | 0.43750 | 0.70587 |
| `L3_online_gru` | 0.44271 | 0.54688 | 0.49734 |
| `L3_reset_control_corrected` | 0.46354 | 0.52604 | 0.51299 |

Key deltas:

```text
L2_window_13 - L2_window_13_current_tiled:
  success: +0.00521
  collision: -0.00521
  mean margin: +0.00771

L2_window_25 - L2_window_25_current_tiled:
  success: -0.00521
  collision: +0.00521
  mean margin: -0.00419

L3_online_gru - L3_reset_control_corrected:
  success: -0.02083
  collision: +0.02083
  mean margin: -0.01565

L3_online_gru - L0_current_masked:
  success: -0.07813
  collision: +0.16146
  mean margin: -0.29255
```

## Classification

M1389 classifies M1388 as:

```text
completed_public_profile_pilot: true
architecture_ranking_claim_allowed: false
finite_window_history_necessity: not_supported
online_gru_hidden_advantage: not_supported
current_frame_substitution_risk: high
profile_scaling_value: low_without_new_task
```

Reason:

```text
L2 is the strongest family by aggregate success, but current-tiled L2 controls
are nearly identical. This supports temporal-GRU/capacity/current-frame
explanations, not finite-window history necessity.

L3 online GRU underperforms corrected reset-control, L0, and L2 in this public
pilot. This is negative evidence for recurrent-hidden utility under the current
fixed-budget task distribution.
```

This does not falsify the whole project. It falsifies the local assumption that
a plain fixed-budget L0/L1/L2/L3 profile pilot on this distribution will reveal
history necessity.

## Supported Claims

M1389 supports:

```text
1. The corrected profile training/evaluation harness is operational.
2. The current fixed-budget public profile pilot is complete and finite.
3. Current-tiled L2 controls remain necessary for interpretation.
4. The tested public distribution does not show meaningful finite-window
   history necessity.
5. The tested public distribution does not show online-GRU hidden advantage.
6. More blind profile scaling is not the highest-leverage next step.
```

## Unsupported Or Falsified Claims

M1389 does not support:

```text
1. L3 online GRU architecture superiority.
2. finite-window history necessity.
3. recurrent-belief advantage.
4. level3 self-identification.
5. private-holdout generalization.
6. paper-level architecture ranking.
```

Local falsified claim:

```text
Running a standard fixed-budget profile pilot on the current distribution is
enough to expose useful online history dependence.
```

## Failure Taxonomy Summary

No structural failure occurred.

Scientific/process classifications:

```text
metric_artifact risk avoided:
  current-tiled and corrected-reset controls were included.

scenario_sampling_failure:
  the current public profile distribution does not make history necessary.

objective_overfit risk avoided:
  no profile was promoted or tuned from these public results.
```

## Public-Gate Overfit Risk

Risk:

```text
medium
```

Reason:

```text
The pilot uses public training and public eval seeds. It is adequate for
debugging the comparison harness and identifying negative trends, but not for
private generalization or paper-level ranking.
```

## Next Branch Decision

Do not run another profile repeat now.

Open:

```text
paper_route_causal_history_necessity_task_design
```

First task:

```text
m1390-paper-route-causal-history-necessity-task-design
```

M1390 should design a task/gate family that makes history causally necessary
instead of hoping standard public profile training reveals it. It should focus
on:

```text
matched-current observations;
same current frame but different past command-response histories;
delayed or wrong history interventions;
warmup response evidence that is not visible in the current frame;
outcome-relevant normal-vs-reset/wrong-history gaps;
source-diverse accepted seeds before corpus export or training.
```

The design may reuse M1377/M1379 temporal source-rich diagnostics as public
input, but must keep their seed-thin limitation explicit.

## Guardrails

M1389 performs no training, PPO, new evaluation, actor update, checkpoint
mutation, promotion, private holdout, threshold relaxation, actor-input
expansion, corpus export, high-fidelity claim, paper-level architecture-ranking
claim, recurrent-belief advantage claim, or level3 self-identification claim.
