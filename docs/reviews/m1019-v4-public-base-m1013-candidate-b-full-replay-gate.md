# m1019-v4-public-base-m1013-candidate-b-full-replay-gate Research Review

## Summary

- Generated at UTC: 20260526T200655Z
- Type: gate
- Gate tier: proof
- Promotion decision: candidate_b_full_replay_gate_pass_route_to_branch_synthesis
- Decision reason: M1019 passes exact temporal retention M267 preflight six public replay source-diverse diagnostics and behavior seeds for Candidate B without PPO promotion or private holdout

## Hypothesis

Candidate B can pass exact temporal retention, six public replay surfaces, source-diverse diagnostics, and behavior seeds after passing M267/M264 preflight.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, docs/m1018-v4-public-base-m1013-candidate-b-full-replay-design.md
- parent_config: configs/m121_human_view_zero_obstacle_relvel.json, experiments/manifests/m1018-v4-public-base-m1013-candidate-b-full-replay-design.json
- parent_objective: run full public proof and behavior gate for the M1013 Candidate B checkpoint
- derived_from: m1018-v4-public-base-m1013-candidate-b-full-replay-design
- blocked_by: Candidate B has passed M267/M264 preflight only and needs exact retention plus full public replay diagnostics
- supersedes: None
- invalidates: None

## Success Criteria

- summary artifact exists
- contract and exact temporal retention are recomputed
- all six public replay surfaces are evaluated
- source-diverse diagnostics are evaluated
- behavior seeds 9505 and 9506 are evaluated
- PPO and promotion remain blocked

## Failure Criteria

- Candidate B fails exact temporal retention
- Candidate B fails any public replay surface
- Candidate B fails behavior retention
- the gate changes actor inputs or uses private holdout

## Evidence Gates

- M1019 must not train
- M1019 must not run PPO
- M1019 must not promote
- M1019 must preserve P0 actor inputs
- M1019 must recompute exact temporal retention
- M1019 must run six public replay surfaces before any promotion discussion
- M1019 must run behavior seeds 9505 and 9506

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not promote Candidate B
- do not change actor inputs
- do not skip exact temporal retention
- do not use cached M1013 exact metrics as the only exact evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1019-v4-public-base-m1013-candidate-b-full-replay-gate
- type: gate
- checkpoint: runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_full_replay_gate_pass_route_to_branch_synthesis
- reason: M1019 passes exact temporal retention M267 preflight six public replay source-diverse diagnostics and behavior seeds for Candidate B without PPO promotion or private holdout

## Next Blocker

m1020-v4-public-base-temporal-sequence-objective-post-candidate-b-synthesis
