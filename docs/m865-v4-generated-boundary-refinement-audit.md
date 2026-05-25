# M865 V4 Generated Boundary Refinement Audit

## Purpose

M865 audits the M864 sparse-useful generated-boundary refinement result before
pair-delta refresh, objective training, PPO, promotion, or another
boundary-generation pass.

The audit question is:

```text
Is M864's sparse generated-boundary surface sufficient to design a limited
pair-delta refresh, or should the branch continue boundary generation first?
```

M865 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Artifact Completeness

M864 produced the required artifacts:

```text
runs/m864_v4_generated_boundary_refinement/summary.json
runs/m864_v4_generated_boundary_refinement/bracket_seed_rows.csv
runs/m864_v4_generated_boundary_refinement/reconstructed_snapshot_rows.csv
runs/m864_v4_generated_boundary_refinement/refinement_rows.csv
runs/m864_v4_generated_boundary_refinement/accepted_refined_boundary_rows.csv
runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv
runs/m864_v4_generated_boundary_refinement/pairability_projection_rows.csv
runs/m864_v4_generated_boundary_refinement/refinement_summary.csv
runs/m864_v4_generated_boundary_refinement/gate_summary.csv
runs/m864_v4_generated_boundary_refinement/rejected_rows.csv
```

Frozen-parameter checks passed:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
```

## Sparse Gate Result

M864 passed the sparse generated-boundary gate:

```text
combined_generated_boundary_rows: 59 >= 32
combined_boundary_new_to_m844_rows: 59 >= 24
combined_unique_source_group_count: 27 >= 20
combined_unique_seed_count: 5 >= 5
combined_unique_fault_family_count: 9 >= 8
combined_pairability_projection_rows: 365 >= 40
```

The refined-only signal was also strong enough:

```text
accepted_refined_boundary_rows: 42 >= 8
accepted_no_m860_boundary_rows: 33 >= 6
unique_refined_source_group_count: 20 >= 6
```

This confirms that M860 generated brackets were not a dead end. Refinement
turned a source-limited generated surface into a sparse-useful boundary surface.

## Residual Limitations

M864 did not pass the strong generated-boundary gate:

```text
combined_generated_boundary_rows: 59 < 60
combined_unique_source_group_count: 27 < 32
combined_unique_seed_count: 5 < 8
```

The surface is also axis-concentrated:

```text
obstacle_lateral_offset: 56
obstacle_timing: 3
obstacle_half_width: 0
```

Seed distribution:

```text
78050: 16
78057: 14
78048: 13
78058: 11
78055: 5
```

Fault-family coverage is broad enough for a limited refresh:

```text
fault families: 9
largest family count: brake_authority_drop = 10
```

The source-group dominance is low:

```text
combined_max_source_group_dominance: 0.067797
```

But seed dominance remains above the earlier strong-style target:

```text
combined_max_seed_dominance: 0.271186
```

## Interpretation

Supported claims:

```text
M864 is a clean no-training positive result.
Sparse generated-boundary coverage is now available.
The combined M860+M864 surface has enough source/fault diversity for a limited
pair-delta refresh design.
Pairability projection is abundant enough to choose source-aware pairs.
```

Unsupported claims:

```text
M864 is strong generated-boundary coverage.
M864 is pair-delta outcome evidence.
M864 is objective-ready self-ID data.
M864 admits PPO.
M864 justifies checkpoint promotion.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  still present as strong-gate seed/source/axis limitations

metric_artifact risk:
  pairability projection must be converted into actual sequence replay before
  any pair-delta claim

contract_violation:
  not observed
```

## Decision

M865 should admit a limited pair-delta refresh design over the M864 combined
generated-boundary rows.

This is justified because:

```text
1. sparse generated-boundary gates passed;
2. pairability projection is large: 365 primary rows;
3. source/fault coverage is broader than the M850 active set;
4. the next scientific question is whether this sparse boundary surface yields
   real pair-delta sequence outcome rows.
```

This does not admit PPO or objective training. The next milestone must be
design-only and should keep the implementation guarded:

```text
no actor update
no M761 update
no PPO
no promotion
pair-delta sequence replay only after design and with explicit gates
```

Decision:

```text
admit_limited_pair_delta_refresh_design
```

Next:

```text
m866-v4-generated-boundary-pair-delta-refresh-design
```
