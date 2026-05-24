# M507 Terminal Boundary Anchor Mining Design

## Purpose

M507 designs the next proof path after M506 showed that selecting from the
existing M504 pair table is still too source-capped.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## M506 Failure Mode

M506 improved the terminal-margin distribution:

```text
M504 targeted rows margin <= 0.50: 4
M506 targeted rows margin <= 0.50: 35

M504 targeted rows margin <= 1.00: 6
M506 targeted rows margin <= 1.00: 76
```

It also retained nonzero wrong-history action signal:

```text
targeted_trajectory_mean: 0.084141
targeted_trajectory_p90:  0.138282
```

But the source-capped surface remained too small:

```text
targeted_pair_count: 101
required:           240
single_label_share: 0.732673
required:        <= 0.70
```

This suggests the M504 pair table is the wrong starting pool. It contains many
low-margin rows and many action-sensitive rows, but not enough rows where both
properties survive source caps.

## Design Choice

The next step should mine terminal-boundary anchors directly.

The selection order becomes:

```text
1. run normal-history M399 rollouts on M502 configs;
2. export low-clearance normal-history anchor states;
3. for each anchor, search source-diverse wrong histories nearby in current
   response/context space;
4. score candidate wrong histories by one-shot action perturbation and short
   horizon margin effect;
5. only then admit outcome-gate candidates.
```

This is different from M503/M504:

```text
M503: match current state first, target capability divergence second.
M504: action sensitivity first, inspect margin second.
M506: low margin from existing pair table first, but still constrained by that
      table's pre-existing pairs.

M508 should build the candidate table from low-margin anchors first.
```

## M508 Implementation Sketch

Implement:

```text
autodrift.terminal_boundary_anchor_miner
```

Inputs:

```text
--checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
--env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json
--env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json
--anchor-seeds 13000,13100,13200,13300,13400,13500
--episodes-per-seed 64
--snapshot-stride 2
--anchor-margin-max 1.0
--candidate-margin-max 2.0
--nearest-k 48
--max-current-distance-quantile 0.05
--short-horizon-steps 8
```

Stage A: Anchor export.

For each normal M399 rollout, collect snapshots where the normal branch has:

```text
normal_min_clearance_margin <= 1.0
not already collision at snapshot
obstacle is visible or within decision window
```

Export:

```text
anchor_id
config
seed
episode
step
obstacle_label
normal_min_clearance_margin
obstacle_distance
obstacle_lateral_offset
current_response/context embedding
hidden state
```

Stage B: Wrong-history candidate search.

For each anchor, search wrong-history snapshots from other seeds/episodes with:

```text
same config preferred, cross-config optional diagnostic
similar current_response_context embedding
different source seed or episode
different hidden/capability proxy where possible
```

Stage C: One-shot replay scoring.

For each candidate pair:

```text
normal branch: start from anchor hidden
wrong branch:  start from anchor observation/state with candidate hidden once
then close loop normally
```

Record:

```text
first_action_distance
action_trajectory_distance_mean
action_trajectory_distance_max
normal_min_clearance_margin
wrong_min_clearance_margin
short_horizon_margin_gap
normal_success / wrong_success / collision / completion
```

## Admission Gate

M508 should only admit an M509 outcome gate if:

```text
anchor_count >= 120
pair_count >= 240
probe_seed_count >= 6
obstacle_label_count >= 2
config_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
single_config_share <= 0.70

rows normal_margin <= 0.50 >= 40
rows normal_margin <= 1.00 >= 100
targeted_trajectory_mean >= 0.04
targeted_trajectory_p90 >= 0.08
```

Outcome-gate admission still requires source-capped rows. Do not relax caps
after seeing M508.

## Fallback

If M508 cannot find enough one-shot wrong-history action signal around natural
low-margin anchors, then the next admissible fallback is obstacle-boundary
projection:

```text
use normal-history trajectory;
move obstacle minimally within the same ego-frame geometry family;
cap longitudinal/lateral projection deltas;
rerun wrong-history outcome gate;
report projection magnitude distribution.
```

This fallback is more artificial than natural anchor mining, so it should only
be used after M508 fails and must be labelled as projection proof, not raw
natural-scenario proof.

## Decision

```text
admit_m508_terminal_boundary_anchor_miner
```

M508 should implement and run anchor-first terminal-boundary mining. It should
not train or promote a checkpoint.
