# m858-v4-boundary-new-to-m844-bracket-trace-audit Research Review

## Summary

- Generated at UTC: 20260525T150442Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_closer_obstacle_source_generation_design
- Decision reason: M858 audits M857 as clean all-safe-wide trace evidence and routes to closer obstacle/source generation before pair-delta replay objective training or PPO

## Hypothesis

M857 cleanly shows boundary-new-to-M844 rows are mostly wide-safe, so the next branch step should design closer obstacle/source generation rather than wider same-axis replay.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m857-v4-boundary-new-to-m844-bracket-trace-implementation.md, runs/m857_v4_boundary_new_to_m844_bracket_trace/summary.json, runs/m857_v4_boundary_new_to_m844_bracket_trace/cause_summary.json, runs/m857_v4_boundary_new_to_m844_bracket_trace/axis_trace_summary.csv, runs/m857_v4_boundary_new_to_m844_bracket_trace/bracket_trace_rows.csv
- parent_config: experiments/manifests/m857-v4-boundary-new-to-m844-bracket-trace-implementation.json
- parent_objective: audit all-safe-wide boundary-new-to-M844 bracket trace result
- derived_from: m857-v4-boundary-new-to-m844-bracket-trace-implementation
- blocked_by: M857 primary boundary-new-to-M844 traces are dominated by all-safe-wide axes with zero extended accepted boundary axes
- supersedes: None
- invalidates: None

## Success Criteria

- M858 writes an audit document for M857
- M858 verifies M857 artifact completeness and frozen checksums
- M858 classifies the all-safe-wide result and failure taxonomy
- M858 selects the next no-training data route
- M858 keeps pair-delta replay, PPO, and promotion blocked

## Failure Criteria

- M858 admits PPO or promotion
- M858 trains actor or residual parameters
- M858 treats trace rows as pair-delta outcome evidence
- M858 ignores M857 primary/control distinction

## Evidence Gates

- M858 must audit M857 before source generation design
- M858 must separate primary boundary-new-to-M844 evidence from recovered controls
- M858 must decide whether all-safe-wide supports closer obstacle/source generation
- M858 must keep pair-delta replay, PPO, and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M858
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat trace rows as pair-delta outcome evidence
- do not ignore the distinction between primary and control trace rows

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m858-v4-boundary-new-to-m844-bracket-trace-audit
- type: gate
- checkpoint: docs/m858-v4-boundary-new-to-m844-bracket-trace-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_closer_obstacle_source_generation_design
- reason: M858 audits M857 as clean all-safe-wide trace evidence and routes to closer obstacle/source generation before pair-delta replay objective training or PPO

## Next Blocker

M857 all-safe-wide result needs audit before closer obstacle/source generation design
