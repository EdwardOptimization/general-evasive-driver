# m853-v4-pair-delta-boundary-expansion-design Research Review

## Summary

- Generated at UTC: 20260525T141204Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: pair_delta_boundary_expansion_design_admit_m854
- Decision reason: M853 designs no-training expanded boundary bracketing over underrepresented source seed and fault families before pair-delta replay

## Hypothesis

Expanded boundary bracketing over underrepresented source/fault/seed families can expose broader pair-delta-positive low-margin states than M850.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m852-v4-source-diverse-sequence-effective-corpus-branch-synthesis.md, docs/m850-v4-pair-delta-focused-source-balanced-mining-implementation.md, runs/m850_v4_pair_delta_focused_source_balanced_mining/summary.json, runs/m850_v4_pair_delta_focused_source_balanced_mining/accepted_pair_delta_rows.csv, runs/m844_v4_source_diverse_sequence_effective_corpus/boundary_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
- parent_config: experiments/manifests/m852-v4-source-diverse-sequence-effective-corpus-branch-synthesis.json
- parent_objective: design expanded boundary bracketing over underrepresented pair-delta source/fault families
- derived_from: m852-v4-source-diverse-sequence-effective-corpus-branch-synthesis
- blocked_by: M850 pair-delta-first mining improves raw yield but remains source-limited
- supersedes: None
- invalidates: None

## Success Criteria

- M853 writes a design document for pair-delta boundary expansion
- M853 defines underrepresented source/fault/seed targets
- M853 defines boundary expansion artifacts and gates
- M853 keeps direct pair-delta evidence separate from learned self-ID proof
- M853 keeps PPO and promotion blocked

## Failure Criteria

- M853 admits PPO or promotion
- M853 trains actor or residual parameters
- M853 ignores M850 source limitations
- M853 designs another replay of the same source-concentrated active set

## Evidence Gates

- M853 must remain design-only
- M853 must target underrepresented pair-delta source seed and fault families
- M853 must define boundary expansion gates before pair-delta replay
- M853 must keep direct sequence evidence separate from learned self-ID proof
- M853 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M853
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat M850 pair-delta rows as learned self-ID proof
- do not tune boundary thresholds around current positives

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m853-v4-pair-delta-boundary-expansion-design
- type: infrastructure
- checkpoint: docs/m853-v4-pair-delta-boundary-expansion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pair_delta_boundary_expansion_design_admit_m854
- reason: M853 designs no-training expanded boundary bracketing over underrepresented source seed and fault families before pair-delta replay

## Next Blocker

pair-delta positives are real but current boundary sources are too concentrated
