# m857-v4-boundary-new-to-m844-bracket-trace-implementation Research Review

## Summary

- Generated at UTC: 20260525T145954Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_boundary_new_to_m844_bracket_trace_all_safe_wide
- Decision reason: M857 traces 132 primary boundary-new-to-M844 source axes with 1924 replay rows and finds 86.36 percent all-safe-wide zero extended accepted boundary axes so audit should route toward closer obstacle/source generation

## Hypothesis

Full parameter/outcome traces over M854 boundary-new-to-M844 no-bracket sources can identify whether the next route should widen axes, generate new sources, shift source steps, or stop the branch.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m856-v4-boundary-new-to-m844-bracket-trace-design.md, runs/m854_v4_pair_delta_boundary_expansion/target_source_rows.csv, runs/m854_v4_pair_delta_boundary_expansion/rejected_rows.csv, runs/m854_v4_pair_delta_boundary_expansion/accepted_boundary_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
- parent_config: experiments/manifests/m856-v4-boundary-new-to-m844-bracket-trace-design.json
- parent_objective: implement no-training trace diagnostic for boundary-new-to-M844 no-bracket sources
- derived_from: m856-v4-boundary-new-to-m844-bracket-trace-design
- blocked_by: M854 boundary-new-to-M844 no-bracket causes are not distinguishable from existing artifacts
- supersedes: None
- invalidates: None

## Success Criteria

- M857 implements bracket trace source selection
- M857 writes full trace and cause artifacts
- M857 verifies actor and residual-head checksums unchanged
- M857 classifies no-bracket causes without pair-delta replay
- M857 keeps PPO and promotion blocked

## Failure Criteria

- M857 trains actor or residual-head parameters
- M857 runs PPO
- M857 promotes a checkpoint
- M857 runs pair-delta sequence replay
- M857 mutates actor input contract

## Evidence Gates

- M857 must implement no-training bracket tracing only
- M857 must target boundary-new-to-M844 source axes
- M857 must write trace rows and cause summaries
- M857 must preserve actor and residual-head checksums
- M857 must not run pair-delta sequence replay, train, or promote

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels or oracle fields to actor input
- do not replay pair-delta sequences in M857
- do not treat trace rows as learned self-ID proof

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m857-v4-boundary-new-to-m844-bracket-trace-implementation
- type: infrastructure
- checkpoint: runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_boundary_new_to_m844_bracket_trace_all_safe_wide
- reason: M857 traces 132 primary boundary-new-to-M844 source axes with 1924 replay rows and finds 86.36 percent all-safe-wide zero extended accepted boundary axes so audit should route toward closer obstacle/source generation

## Next Blocker

boundary-new-to-M844 traces are dominated by all-safe-wide source axes, so closer obstacle/source generation needs audit and design
