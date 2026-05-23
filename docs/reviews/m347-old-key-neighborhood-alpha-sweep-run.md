# m347-old-key-neighborhood-alpha-sweep-run Research Review

## Summary

- Generated at UTC: 20260523T100715Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m348_exact_source_diverse_probe_for_m335_a010
- Decision reason: M347 targeted old-key sweep finds alpha 0.01 is largest passing alpha and alpha 0.02 first fails due accepted-case regression; no promotion

## Hypothesis

The replayable old-key neighborhood gate may allow a larger interpolation alpha than the old singleton 9944 floor while still rejecting the repaired endpoint direction.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_02.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_05.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_1.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_2.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_1.pt
- parent_dataset: runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv
- parent_config: experiments/manifests/m346-old-key-neighborhood-alpha-sweep-design.json, docs/m346-old-key-neighborhood-alpha-sweep-design.md
- parent_objective: run no-PPO old-key neighborhood alpha sweep before more PPO
- derived_from: m346-old-key-neighborhood-alpha-sweep-design
- blocked_by: m346-old-key-neighborhood-alpha-sweep-design
- supersedes: None
- invalidates: None

## Success Criteria

- m335_a0_0075 replay reproduces old-key neighborhood pass
- candidate alphas are evaluated with replayable old-key metrics
- largest passing alpha and first failing alpha are reported
- failure types are classified before any PPO
- research validation passes

## Failure Criteria

- alpha sweep cannot reproduce m335_a0_0075 pass
- guard replay rows do not cover the 40 compact cases
- 9944 diagnostic is missing
- thresholds are changed after seeing results
- PPO or promotion is attempted

## Evidence Gates

- export exact compact reference cases from M341 compact corpus
- run critical_key_replay_guard or equivalent replay for selected M335 alpha checkpoints
- run old_key_neighborhood_replay_gate for each candidate versus m335_a0_0075
- report largest passing alpha and first failing alpha
- do not run PPO or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use static selected/endpoint columns as future candidate proof
- do not lower old-key neighborhood thresholds
- do not hide 9944 diagnostic
- do not skip replay reproduction of m335_a0_0075
- do not promote from alpha sweep alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m347-old-key-neighborhood-alpha-sweep-run
- type: gate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m348_exact_source_diverse_probe_for_m335_a010
- reason: M347 targeted old-key sweep finds alpha 0.01 is largest passing alpha and alpha 0.02 first fails due accepted-case regression; no promotion

## Next Blocker

m348-exact-source-diverse-probe-for-m335-a010
