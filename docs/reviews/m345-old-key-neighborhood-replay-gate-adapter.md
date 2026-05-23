# m345-old-key-neighborhood-replay-gate-adapter Research Review

## Summary

- Generated at UTC: 20260523T094608Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m346_old_key_neighborhood_alpha_sweep_design
- Decision reason: M345 implements replayable old-key candidate metrics from guard_results; m335_a0075 passes with 0 regressions and m335_repaired fails with 15 accepted regressions

## Hypothesis

A replayable adapter can convert the M341 old-key neighborhood surface into a candidate-level proof gate so future PPO proposals can be checked without returning to singleton 9944 veto dominance.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv, runs/m343_old_key_neighborhood_gate_probe/summary.json
- parent_config: experiments/manifests/m344-old-key-neighborhood-policy-integration-design.json, docs/m344-old-key-neighborhood-policy-integration-design.md
- parent_objective: make the old-key neighborhood gate replayable for arbitrary future candidate checkpoints
- derived_from: m344-old-key-neighborhood-policy-integration-design
- blocked_by: m344-old-key-neighborhood-policy-integration-design
- supersedes: None
- invalidates: None

## Success Criteria

- future-candidate gate schema is implemented or concretely formalized
- M335 alpha is reproduced as pass under replayable candidate metrics
- M335 repaired endpoint is reproduced as fail or repair-needed
- tests cover schema validation and pass/fail threshold aggregation
- research validation passes

## Failure Criteria

- adapter only reads saved selected/endpoint columns and cannot evaluate future candidates
- adapter hides M133/9944 diagnostic visibility
- adapter changes actor input contract
- adapter runs PPO or promotes a checkpoint

## Evidence Gates

- implement or formalize replayable candidate evaluation for M341 compact old-key rows
- reproduce M335 alpha pass and M335 repaired endpoint failure or repair-needed classification
- keep 9944 diagnostic visible
- add focused tests for replayable schema and threshold aggregation
- do not run PPO or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not claim M343 static saved columns certify future checkpoints
- do not remove 9944 diagnostic visibility
- do not lower old-key neighborhood thresholds
- do not change actor inputs
- do not train or repair a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m345-old-key-neighborhood-replay-gate-adapter
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m346_old_key_neighborhood_alpha_sweep_design
- reason: M345 implements replayable old-key candidate metrics from guard_results; m335_a0075 passes with 0 regressions and m335_repaired fails with 15 accepted regressions

## Next Blocker

m346-old-key-neighborhood-alpha-sweep-design
