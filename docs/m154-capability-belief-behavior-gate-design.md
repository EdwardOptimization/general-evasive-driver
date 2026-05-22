# M154 Capability-Belief Behavior Gate Design

Date: 2026-05-22

## Question

M153 proved that the capability-belief target can be optimized through the
current `human_view_online_gru` response hidden state. M154 defines the gate
that must pass before any capability-belief PPO continuation or actor promotion.

This is a gate-design milestone. It does not run a candidate checkpoint because
no capability-belief trained driver candidate exists yet.

## Implementation

New module:

```text
src/autodrift/capability_belief_behavior_gate_design.py
```

New tests:

```text
tests/test_capability_belief_behavior_gate_design.py
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_belief_behavior_gate_design \
  --candidate-name capability_belief_candidate \
  --candidate-checkpoint '<capability_belief_candidate_checkpoint.pt>' \
  --baseline-checkpoint runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --m118-pairs-csv runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv \
  --behavior-episodes 80 \
  --behavior-seeds 9503,9504 \
  --strict-surface-seeds 9900,9920 \
  --run-dir runs/m154_capability_belief_behavior_gate_design
```

Artifacts:

```text
runs/m154_capability_belief_behavior_gate_design/gate_spec.json
runs/m154_capability_belief_behavior_gate_design/gate_checklist.csv
runs/m154_capability_belief_behavior_gate_design/command_plan.csv
runs/m154_capability_belief_behavior_gate_design/summary.json
```

## Gate Stages

M154 pre-registers eight required stages:

| Stage | Kind | Command count | Purpose |
| --- | --- | ---: | --- |
| actor input contract | contract | 0 | reject oracle/input leakage |
| behavior retention | benchmark | 2 | preserve M142/M133 behavior surface |
| response history interventions | benchmark ablation | 0 | require reset/zero/no-action accounting |
| critical-key replay | critical key guard | 1 | protect M141 near-threshold key |
| matched-history action gate | wrong-history action | 1 | preserve action-level wrong-history dependence |
| matched-history outcome gate | wrong-history outcome | 1 | require rollout outcome degradation |
| strict proof surface | snapshot-bank relocation | 2 | preserve M133/M142 proof surface |
| promotion boundary | decision boundary | 0 | block driver promotion from gate design |

Required interventions:

```text
reset_recurrent_state
zero_current_response
zero_all_response
zero_action_history
wrong_matched_history
delayed_history
```

## Pre-Registered Thresholds

Actor contract:

```text
actor_obs_dim = 72
actor_encoder = human_view_online_gru
forbidden actor fields include:
  mu, mass, tire_stiffness, brake_scale, actuator_tau,
  oracle_feasibility, obstacle_label, speed_ref, beta_target,
  path_error, heading_error, TTC, required_clearance
```

Behavior retention:

```text
normal_success_min = baseline_success - 0.0125
normal_clearance_margin_mean_min = baseline_clearance_margin_mean - 0.02
collision_rate_max = baseline_collision_rate + 0.0125
behavior_seed_count_min = 2
```

Response-history interventions:

```text
zero_current_success_gap_min = 0.05
zero_all_success_gap_min = 0.05
reset_success_gap_min = 0.00
zero_action_success_gap_min_for_ppo_admission = 0.00
zero_action_success_gap_min_for_driver_claim = 0.05
```

Critical-key replay:

```text
protected_key = 9944|perturbed|28|28
accepted_cases_min = 1 / 1
margin_gap_min = 0.005
```

Matched-history action gate:

```text
wrong_matched_history_physical_pairs_min = 100
wrong_matched_history_above_threshold_fraction_min = 0.70
wrong_matched_history_closer_to_right_fraction_min = 0.65
```

Matched-history outcome gate:

```text
wrong_history_margin_gap_mean_min = 0.005
wrong_history_success_drop_pairs_min = 6
selected_physical_pairs_min = 6
```

Strict proof surface:

```text
seed_9900_selected_physical_pairs_min = 10
seed_9900_selected_seeds_min = 8
seed_9920_selected_physical_pairs_min = 9
seed_9920_selected_seeds_min = 8
m62_control_selected_physical_pairs_max = 0
```

## Interpretation

M154 deliberately keeps the next step conservative. M152/M153 prove only that a
capability-belief target is learnable from deployable P0 history and recurrent
response hidden state. They do not prove behavior retention, wrong-history
outcome degradation, or rollout-margin proof-surface survival.

The gate therefore blocks PPO or driver promotion unless a future candidate
passes all required stages.

## Decision

M154 completes as a positive gate-design milestone:

```text
gate_stage_count = 8
required_stage_count = 8
decision_rule = admit guarded PPO only if all required stages pass;
                never promote driver from M154 alone
```

The next implementation step can create a capability-belief candidate, but it
must be evaluated against this gate before it is treated as PPO-ready or
driver-like.
