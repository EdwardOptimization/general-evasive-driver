# M605 Grounded Capability-Action Target Mining Design

## Purpose

M605 designs target mining for the M604 belief-only gaps.

Question:

```text
Can rows where capability belief moves but action does not be grounded in
simulator-validated action targets?
```

This milestone is design-only:

```text
no implementation
no training
no PPO
no checkpoint promotion
```

## Source

M604 found:

```text
real-history belief-only gaps: 262
```

Distribution:

| Surface | Variant | Candidates |
| --- | --- | ---: |
| fresh | `shuffled_history` | `84` |
| fresh | `delayed_history` | `24` |
| fresh | `wrong_matched_history` | `8` |
| OOD | `shuffled_history` | `77` |
| OOD | `wrong_matched_history` | `49` |
| OOD | `delayed_history` | `20` |

The strongest semantically clean subset is OOD `wrong_matched_history`, with
`49` candidates, including `28` `future_lateral_accel_response` rows and `17`
`future_yaw_response` rows.

## Principle

A `belief_only_gap` is not an action label.

It means:

```text
capability belief changed;
actor action did not.
```

It does not tell us:

```text
which action is better;
whether more steer, more brake, brake release, or throttle is needed;
whether the row is near a safety boundary;
whether action movement improves closed-loop outcome.
```

Therefore M606 must mine grounded targets with simulator rollouts. No future
optimizer may use M604 candidate rows directly as action-separation labels.

## Target Mining Scope

M606 should start with a bounded smoke:

```text
source rows: M604 candidate_for_grounding rows
priority order:
  1. OOD wrong_matched_history lateral/yaw rows
  2. fresh wrong_matched_history rows
  3. source-diverse shuffled_history rows
  4. delayed_history rows
max_rows_per_surface_variant_target: 16
```

Use the original surface configs:

```text
fresh: configs/ppo_m541_matched_l3_variance_4096.json
OOD:   configs/eval_m574_moderate_ood_l3.json
```

For each selected row:

1. Reconstruct the current BC5660 environment state at `left_seed/left_step`.
2. Reconstruct the current normal recurrent hidden.
3. Compute the base actor action.
4. Evaluate a local first-action override grid.
5. Continue rollout under the same BC5660 policy.
6. Accept only candidates that improve a simulator metric and stay in a trust
   region.

## Local Action Grid

Use a small first grid:

```text
steer_delta    in {-0.08, -0.04, -0.02, 0, +0.02, +0.04, +0.08}
throttle_delta in {-0.06, -0.03, 0, +0.03}
brake_delta    in {-0.08, -0.04, -0.02, 0, +0.02, +0.04, +0.08}
```

This gives `196` candidates per row before clipping. The target miner should
record every candidate rollout, not only the selected target.

The first grid intentionally includes brake release and brake increase because
handling-limit evasive behavior may require either:

```text
more braking for low-speed/straight-line mitigation;
brake release to restore lateral authority;
steer/yaw adjustment for drift or avoidance entry.
```

## Rollout Horizon

Use a short continuation first:

```text
max_continuation_steps = 40
```

If the episode terminates earlier, record the terminal reason. If the horizon
ends without termination, score the short-horizon minimum clearance margin and
progress proxy.

## Acceptance Criteria

For each row, compute the baseline rollout from the base action:

```text
baseline_margin
baseline_collision
baseline_road_departure
baseline_terminal_reason
```

Accept a candidate action only if all hard conditions pass:

```text
action_l2 <= 0.10
candidate_road_departure == false
candidate_spin_or_invalid == false
```

Then require at least one utility condition:

```text
candidate avoids collision when baseline collides
or candidate_margin >= baseline_margin + 0.02
or candidate_risk_score <= baseline_risk_score - 0.05
```

For a smoke run, risk score can be a simple logged metric:

```text
risk_score =
  collision_penalty
  + road_departure_penalty
  - clipped_clearance_margin
```

M606 should not hide rows with no accepted target. It should write them to an
unrecovered/unaccepted artifact.

## Branch Preservation

For each accepted normal-branch target, also export the base variant action as
a guard:

```text
observation
normal_hidden
variant_hidden
target_action
normal_base_action
variant_base_action
capability_z_distance
action_distance
source row id
weight
```

The future optimizer can then:

```text
move normal branch toward target_action
anchor normal branch near base when no target exists
anchor variant branch unless a separate grounded target exists
```

This prevents the old failure mode:

```text
normal branch repaired;
wrong-history branch also becomes safe by accident.
```

## Weighting

Initial target weight:

```text
weight =
  min(4.0, max(1.0, margin_improvement / 0.02))
  * source_diversity_weight
```

Keep source-diversity weighting simple in M606:

```text
source_diversity_weight = 1.0 / sqrt(rows_from_same_left_seed_variant_target)
```

Do not let one seed/step dominate the target corpus.

## Artifacts

M606 should write:

```text
runs/m606_grounded_capability_action_target_miner/summary.json
runs/m606_grounded_capability_action_target_miner/target_candidates.csv
runs/m606_grounded_capability_action_target_miner/accepted_targets.csv
runs/m606_grounded_capability_action_target_miner/unaccepted_rows.csv
runs/m606_grounded_capability_action_target_miner/target_corpus.npz
```

The NPZ should contain only deployable actor-facing tensors and training
targets:

```text
observation
normal_hidden
variant_hidden
target_action
normal_base_action
variant_base_action
weight
row_id
```

It must not contain hidden simulator parameters or privileged actor inputs.

## M606 Pass/Fail

M606 should pass as an implementation milestone if it:

```text
writes the required artifacts;
records all candidate rollouts;
records no-training/no-PPO/no-promotion flags;
proves labels do not enter actor inputs;
passes focused tests and research validation.
```

Target-mining branch admission should require:

```text
accepted_targets >= 8 in smoke
accepted source left_seed count >= 3
accepted variants include at least one of:
  wrong_matched_history
  shuffled_history
mean accepted margin improvement >= 0.02
```

If these fail, the result is still useful. The next branch should be:

```text
terminal-boundary candidate refresh
or history-length observability audit
```

not actor training.

## Forbidden Shortcuts

Do not:

- train actor or recurrent modules;
- run PPO;
- promote any checkpoint;
- use M604 candidates directly as action labels;
- use hidden parameters or oracle labels as actor inputs;
- tune private holdout rows;
- hide unaccepted rows.

## Decision

```text
grounded_capability_action_target_mining_design_admit_m606
```

M605 passes because it pre-registers simulator-grounded target mining, action
trust regions, acceptance criteria, artifacts, and next-branch logic before any
action-coupling optimizer.

## Next

```text
M606: implement grounded capability-action target miner.
```
