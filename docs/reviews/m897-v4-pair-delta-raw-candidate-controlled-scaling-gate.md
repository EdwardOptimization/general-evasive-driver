# m897-v4-pair-delta-raw-candidate-controlled-scaling-gate Research Review

## Summary

- Generated at UTC: 20260525T202017Z
- Type: gate
- Gate tier: proof
- Promotion decision: raw_candidate_controlled_scaling_gate_pass
- Decision reason: M897 passes exact first full replay and behavior gates for both raw objective-only candidates with about 10x alpha_0_1 clearance movement but no success gain

## Hypothesis

The larger raw objective-only candidates may remain proof-safe under exact-first replay/proof evaluation and provide a more meaningful effect-size budget than alpha_0_1.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m896-v4-pair-delta-controlled-scaling-replay-design.md, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m896-v4-pair-delta-controlled-scaling-replay-design.json
- parent_objective: execute exact-first controlled replay/proof gates for larger raw objective-only candidates
- derived_from: m896-v4-pair-delta-controlled-scaling-replay-design
- blocked_by: raw candidates have larger effect-size budget but no exact-first closed-loop replay evidence
- supersedes: None
- invalidates: None

## Success Criteria

- both exact rechecks pass
- first replay gates pass for both raw candidates
- all six replay/proof surfaces pass for both raw candidates if full replay runs
- behavior seeds 9505 and 9506 do not regress if behavior runs
- M897 keeps PPO and promotion blocked

## Failure Criteria

- any exact recheck fails
- any first replay gate fails
- any full replay surface fails
- behavior success or termination regresses
- M897 promotes or runs PPO

## Evidence Gates

- exact objective recheck for both raw candidates
- first replay gates M183/M170 and M267/M264 for both raw candidates
- all six replay/proof surfaces for both raw candidates if first gates pass
- behavior seeds 9505 and 9506 if full replay passes
- no PPO or promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not skip exact recheck before replay
- do not skip first replay gates before full replay
- do not lower replay thresholds after seeing failures
- do not claim public-base improvement from raw-candidate retention

## Failure Taxonomy

- proof_washout
- behavior_regression
- objective_overfit
- metric_artifact
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m897-v4-pair-delta-raw-candidate-controlled-scaling-gate
- type: gate
- checkpoint: runs/m897_raw_controlled_scaling_full_replay_gate/summary.json
- success_rate: 0.8125
- termination_rate: 0.1875
- clearance_margin_mean: 1.477136
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: raw_candidate_controlled_scaling_gate_pass
- reason: M897 passes exact first full replay and behavior gates for both raw objective-only candidates with about 10x alpha_0_1 clearance movement but no success gain

## Next Blocker

Raw objective-only candidates have not yet run exact-first controlled replay/proof gates
