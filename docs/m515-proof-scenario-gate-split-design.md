# M515 Proof/Scenario Gate Split Design

## Purpose

M515 designs a pre-registered split between mechanism proof gates and broad
scenario-distribution gates after M514 confirms that projected-label diversity
does not overlap terminal-boundary low-margin rows.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## Motivation

M514 found:

```text
low-margin non-unavoidable rows: 0
non_unavoidable_min_normal_margin: 6.505553
```

This means a single gate requiring both:

```text
terminal-boundary low margin
and projected scenario-label diversity
```

is not well-posed for the current projection family. Low-margin rows are the
right surface for mechanism proof, while label diversity is the right property
for broad scenario distribution.

## Design Choice

Split validation into two gates.

### Gate A: Mechanism Proof Gate

Purpose:

```text
Does wrong command-response history change actions or margins at
terminal-boundary states?
```

Required diversity:

```text
pair_count >= 240
probe_seed_count >= 6
target_count >= 2
config_count >= 2
projected_obstacle_bucket_count >= 8
projection_bucket_count >= 8
single_seed_share <= 0.50
single_config_share <= 0.70
single_target_share <= 0.70
single_obstacle_bucket_share <= 0.35
single_projection_bucket_share <= 0.35
```

Required boundary/action signal:

```text
rows normal_margin <= 0.50 >= 40
rows normal_margin <= 1.00 >= 100
targeted_trajectory_mean >= 0.04
targeted_trajectory_p90 >= 0.08
or margin_gap_mean >= 0.02
```

Projected scenario-label diversity is recorded but not required for Gate A,
because M514 shows it is structurally separated from low-margin boundary rows
in this task family.

### Gate B: Scenario Distribution Gate

Purpose:

```text
Does the same checkpoint remain broadly useful across scenario labels and
geometry families?
```

Required diversity:

```text
scenario_count >= 256
probe_seed_count >= 6
obstacle_label_count >= 3 when the generator supports it
config_count >= 2
projected_or_natural_label_distribution reported
```

Metrics:

```text
success_rate
collision_rate
road_departure_rate
spin_rate
clearance_margin_mean/p10
termination_reason histogram
normal vs reset/zero/wrong history diagnostic deltas
```

Gate B is not allowed to tune or repair proof rows. It is for broad evidence and
later promotion, not for mechanism-surface admission.

## M516 Implementation Target

M516 should implement a mechanism-proof selector over M514 scored rows.

Inputs:

```text
runs/m514_projected_label_margin_conflict_audit/scored_pairs.csv
```

Selection should require:

```text
normal_margin <= 2.0
soft wrong-history action signal
source diversity across seed/config/target
geometry diversity across obstacle and projection buckets
```

Output:

```text
runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv
runs/m516_boundary_mechanism_projection_selector/summary.json
```

M516 may admit a downstream outcome gate only if Gate A passes. It must not
claim scenario-label diversity from the mechanism proof rows.

## Forbidden Shortcuts

Do not:

```text
call this a relaxation of M512;
claim mechanism rows prove scenario-label generalization;
use scenario labels as actor inputs;
train or promote from M516;
skip geometry bucket diversity.
```

## Decision

```text
admit_m516_boundary_mechanism_projection_selector
```

Next blocker:

```text
m516-boundary-mechanism-projection-selector
```
