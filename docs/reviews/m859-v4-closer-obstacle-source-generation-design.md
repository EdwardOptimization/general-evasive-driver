# m859-v4-closer-obstacle-source-generation-design Research Review

## Summary

- Generated at UTC: 20260525T151148Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: closer_obstacle_source_generation_design_admit_m860
- Decision reason: M859 designs no-training closer obstacle/source generation from M857 all-safe-wide traces with separate all-safe and all-collision routes before pair-delta replay

## Hypothesis

M857 all-safe-wide traces justify a no-training closer obstacle/source generation design to create genuinely new low-margin boundary rows before pair-delta mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m858-v4-boundary-new-to-m844-bracket-trace-audit.md, runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json, runs/m857_v4_boundary_new_to_m844_bracket_trace/cause_summary.json, runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv, runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv
- parent_config: experiments/manifests/m858-v4-boundary-new-to-m844-bracket-trace-audit.json
- parent_objective: design closer obstacle/source generation from all-safe-wide boundary-new-to-M844 traces
- derived_from: m858-v4-boundary-new-to-m844-bracket-trace-audit
- blocked_by: M857 all-safe-wide primary traces show current boundary-new-to-M844 source pool is too far from low-margin boundary
- supersedes: None
- invalidates: None

## Success Criteria

- M859 writes a design document for closer obstacle/source generation
- M859 defines separate routes for all-safe-wide and all-collision trace subsets
- M859 defines accepted boundary artifacts and gates
- M859 keeps direct trace evidence separate from learned self-ID proof
- M859 keeps pair-delta replay, PPO, and promotion blocked

## Failure Criteria

- M859 admits PPO or promotion
- M859 trains actor or residual parameters
- M859 ignores M857 all-safe-wide evidence
- M859 designs pair-delta replay before accepted new-source boundary generation

## Evidence Gates

- M859 must remain design-only
- M859 must use M857 traces to route all-safe-wide and all-collision subsets differently
- M859 must design no-training source/obstacle generation before pair-delta replay
- M859 must keep actor/residual mutation, PPO, and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M859
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat M857 trace rows as learned self-ID proof
- do not run pair-delta sequence replay before generating a broader low-margin boundary surface

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m859-v4-closer-obstacle-source-generation-design
- type: infrastructure
- checkpoint: docs/m859-v4-closer-obstacle-source-generation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: closer_obstacle_source_generation_design_admit_m860
- reason: M859 designs no-training closer obstacle/source generation from M857 all-safe-wide traces with separate all-safe and all-collision routes before pair-delta replay

## Next Blocker

M857 all-safe-wide traces require closer obstacle/source generation design before more boundary mining
