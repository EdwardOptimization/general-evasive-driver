# M834 V4 Full Wrong-History Response Intervention Design

## Purpose

M834 designs the next no-training diagnostic after M833 audited hidden-only
wrong-history injection as too weak even on near-boundary pairs.

The design question is:

```text
Does the actor's counterfactual self-ID signal live in recurrent hidden memory,
the explicit current ego-response/action stream, or neither?
```

M834 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M832 fixed the earlier boundary slack:

```text
accepted_boundary_rows: 39
boundary_margin_min: 0.0000494
boundary_margin_median: 0.009952
near_boundary_pair_rows: 60
```

but hidden-only wrong-history remained weak:

```text
wrong-hidden first-action max: 0.00665 < 0.014
wrong-hidden margin gap max:  0.0000369 << 0.01
accepted wrong-history rows:  0
```

This means the next control variable should not be simply more hidden-only
replay. The actor may be dominated by the current response/action part of the
observation frame.

## Actor Contract

The deployable P0 observation contract remains unchanged:

```text
0-8    ego response:
       vx, vy, yaw_rate, ax, ay, steer_angle, steer_rate,
       throttle_actuator_state, brake_actuator_state

9-11   previous physical commands:
       previous steer, previous throttle, previous brake

12-43  road boundary points

44-71  obstacle slots
```

M835 must not add hidden parameters, fault labels, oracle feasibility, TTC, path
tracking errors, slip, tire force, or controller-mode inputs.

The new interventions are offline counterfactual corruptions of deployable
fields only. They are diagnostics, not new actor inputs.

## Intervention Matrix

M835 should replay the M832 near-boundary pairs with these variants:

```text
normal:
  left observation + left hidden

wrong_hidden_only:
  left observation + right hidden
  This is the M832 baseline.

wrong_ego_response_obs:
  left context + right obs[0:9] + left obs[9:12] + left hidden

wrong_action_history_obs:
  left context + left obs[0:9] + right obs[9:12] + left hidden

wrong_response_action_obs:
  left context + right obs[0:12] + left hidden

wrong_ego_response_hidden:
  left context + right obs[0:9] + left obs[9:12] + right hidden

wrong_action_history_hidden:
  left context + left obs[0:9] + right obs[9:12] + right hidden

wrong_response_action_hidden:
  left context + right obs[0:12] + right hidden
```

Existing ablations should remain as references:

```text
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
command_shift_obs
response_delay_obs
```

Zero-command rows must stay separate. A response/history intervention does not
count as wrong-history proof if the same row is explained only by zero-command
ablation.

## Data Source

M835 should reuse M832 artifacts:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
```

The implementation should join each pair's left/right candidate IDs to M832
`accepted_boundary_rows.csv`, then reconstruct the left/right snapshots using
M825 source rows and candidate plans.

No new source generation is required in M835.

## Replay Semantics

For a pair `(left, right)`:

```text
env = relocated left env
scene/context = left road and obstacle geometry
rollout dynamics = left fault/source dynamics
```

Only diagnostic policy inputs are altered according to the intervention matrix.
The environment remains left-side so degradation is measured against the left
normal outcome.

For response/action observation swaps:

```text
obs[0:9]   ego response segment
obs[9:12]  previous-command segment
obs[12:72] left scene context, unchanged
hidden     left or right recurrent hidden depending on variant
```

The intervention should apply at least at the first policy step. If extended
over the rollout, it must be logged as a separate mode:

```text
first_step_only
rolling_wrong_response
```

M835 should start with `first_step_only` to isolate action selection at the
matched current state.

## Accepted Row Classes

### Primary Response-History Rows

Required:

```text
normal_success == true
normal_collision == false
normal_margin <= 0.05
variant in {
  wrong_response_action_obs,
  wrong_response_action_hidden,
  wrong_ego_response_hidden,
  wrong_action_history_hidden
}
variant_margin_gap_from_normal >= 0.01
first_action_l2_vs_normal >= 0.014
or success_drop_from_normal == true
```

### Component Attribution Rows

Rows should be retained separately when only one component is causal:

```text
ego_response_only:
  wrong_ego_response_obs or wrong_ego_response_hidden passes

action_history_only:
  wrong_action_history_obs or wrong_action_history_hidden passes

hidden_only:
  wrong_hidden_only passes

response_plus_hidden_only:
  wrong_response_action_hidden passes but each single component fails
```

Component rows are diagnostics unless source/fault diversity gates pass.

### Mitigation Rows

If both histories collide but the wrong intervention worsens finite margin:

```text
variant_margin_gap_from_normal >= 0.02
```

then retain as mitigation diagnostics. Mitigation rows do not count as primary
self-ID proof.

## Pass/Fail Gates

Primary pass:

```text
accepted_primary_response_history_rows >= 80
unique_left_seeds >= 8
unique_right_seeds >= 8
unique_fault_family_pairs >= 6
unique_warmup_pairs >= 2
unique_onset_pairs >= 3
max_seed_share <= 0.25
max_fault_pair_share <= 0.35
```

Sparse positive diagnostic:

```text
20 <= accepted_primary_response_history_rows < 80
and at least 4 fault-family pairs
and action/margin gaps are not zero-command dominated
```

Clean negative:

```text
all full-response variants remain below action and margin thresholds
```

Zero-command dominated:

```text
zero_command_obs passes more rows or larger gaps than wrong-response variants
and wrong-response variants do not pass independently
```

Contract violation:

```text
actor/residual-head checksums change
or hidden params/fault labels/oracle fields enter actor input
```

## Required Artifacts

M835 should write:

```text
response_intervention_pair_rows.csv
response_intervention_replay_rows.csv
accepted_primary_response_history_rows.csv
accepted_component_attribution_rows.csv
accepted_mitigation_rows.csv
variant_summary.csv
component_summary.csv
diversity_summary.json
gate_summary.csv
summary.json
```

The summary must include:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

## Interpretation Rules

If `wrong_hidden_only` stays weak but `wrong_response_action_obs` is strong:

```text
The actor is response-frame sensitive, but current evidence still does not
prove recurrent memory self-ID.
```

If `wrong_response_action_hidden` is strong and single components are weak:

```text
The actor may use hidden and current response jointly; this is the best outcome
for this diagnostic route.
```

If all wrong-response variants remain weak:

```text
The M568/M761 family likely lacks the required counterfactual response-history
sensitivity, and the branch should pivot toward objective/architecture evidence
rather than more data mining.
```

## Decision

Decision:

```text
full_wrong_history_response_intervention_design_admit_m835
```

Next:

```text
m835-v4-full-wrong-history-response-intervention-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and threshold relaxation remain blocked.
