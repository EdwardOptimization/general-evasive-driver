# m893-v4-enriched-pair-delta-fresh-seed-replay-proof-gate Research Review

## Summary

- Generated at UTC: 20260525T200533Z
- Type: gate
- Gate tier: proof
- Promotion decision: v4_enriched_pair_delta_fresh_seed_replay_proof_gate_pass
- Decision reason: M893 repeats the M889 proof-gate positive for fresh seed M891 alpha_0_1 with exact recheck six replay surfaces and behavior seeds passing versus M568

## Hypothesis

The M891 seed-10887 alpha_0_1 exact-admissible objective-only checkpoint can preserve M568-relative replay/proof surfaces and behavior seeds without PPO or promotion.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m892-v4-enriched-pair-delta-objective-only-fresh-seed-repeat-audit.md, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m892-v4-enriched-pair-delta-objective-only-fresh-seed-repeat-audit.json
- parent_objective: run exact recheck and closed-loop replay/proof gates for M891 alpha_0_1
- derived_from: m892-v4-enriched-pair-delta-objective-only-fresh-seed-repeat-audit
- blocked_by: M891 repeated exact objective admissibility but its candidate has not run replay/proof gates
- supersedes: None
- invalidates: None

## Success Criteria

- exact recheck passes for M891 alpha_0_1
- all six replay/proof surfaces pass versus M568
- behavior seeds 9505 and 9506 do not regress if behavior is run
- fallback alpha handling is recorded if needed
- M893 keeps promotion and PPO blocked

## Failure Criteria

- exact recheck regresses holdouts
- any replay surface fails
- behavior success or termination regresses
- M893 promotes or runs PPO

## Evidence Gates

- exact objective recheck for M891 alpha_0_1 versus M568 base
- six public replay surfaces pass versus M568 base
- behavior seeds 9505 and 9506 retain M568-level success and termination if replay passes
- fallback alpha_0_05 handling is recorded if alpha_0_1 fails
- no PPO or promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not skip exact recheck before replay
- do not lower replay thresholds after seeing failures
- do not claim generalization from public replay surfaces

## Failure Taxonomy

- proof_washout
- objective_overfit
- behavior_regression
- metric_artifact
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m893-v4-enriched-pair-delta-fresh-seed-replay-proof-gate
- type: gate
- checkpoint: runs/m893_m891_a010_replay_proof_gate/summary.json
- success_rate: 0.8125
- termination_rate: 0.1875
- clearance_margin_mean: 1.472736
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_enriched_pair_delta_fresh_seed_replay_proof_gate_pass
- reason: M893 repeats the M889 proof-gate positive for fresh seed M891 alpha_0_1 with exact recheck six replay surfaces and behavior seeds passing versus M568

## Next Blocker

M891 alpha_0_1 exact-admissible repeat has not run replay/proof gates
