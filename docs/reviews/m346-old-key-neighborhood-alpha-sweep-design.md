# m346-old-key-neighborhood-alpha-sweep-design Research Review

## Summary

- Generated at UTC: 20260523T094926Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m347_old_key_neighborhood_alpha_sweep_run
- Decision reason: M346 designs a no-PPO alpha sweep over M335 interpolation checkpoints using exact compact reference cases and replayable old-key neighborhood gate metrics

## Hypothesis

A no-PPO alpha sweep using the replayable old-key neighborhood gate can determine whether the M335 repaired direction has a larger acceptable trust region than the old singleton 9944 floor allowed.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_02.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv, runs/m345_old_key_neighborhood_replay_gate_alpha/summary.json, runs/m345_old_key_neighborhood_replay_gate_repaired/summary.json
- parent_config: experiments/manifests/m345-old-key-neighborhood-replay-gate-adapter.json, docs/m345-old-key-neighborhood-replay-gate-adapter.md
- parent_objective: test whether the replayable distributional old-key gate allows more interpolation movement than the singleton 9944 floor
- derived_from: m345-old-key-neighborhood-replay-gate-adapter
- blocked_by: m345-old-key-neighborhood-replay-gate-adapter
- supersedes: None
- invalidates: None

## Success Criteria

- document alpha candidates and gate order
- define critical_key_replay_guard or equivalent replay commands for compact old-key rows
- define replayable gate commands using old_key_neighborhood_replay_gate
- state acceptance and rejection thresholds before running the sweep
- research validation passes

## Failure Criteria

- design skips replayable old-key gate
- design treats static M343 selected/endpoint columns as future candidate proof
- design allows promotion from alpha sweep alone
- design starts PPO before old-key alpha sweep is evaluated

## Evidence Gates

- design a no-PPO alpha sweep over M335 interpolation checkpoints
- use replayable old-key neighborhood gate metrics
- keep exact and source-diverse gates in the admission order
- state which alphas are evaluated and how failures are classified
- do not train or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower old-key neighborhood thresholds
- do not hide singleton 9944 diagnostic
- do not claim alpha-sweep success before replay rows exist
- do not change actor inputs
- do not run PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m346-old-key-neighborhood-alpha-sweep-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m347_old_key_neighborhood_alpha_sweep_run
- reason: M346 designs a no-PPO alpha sweep over M335 interpolation checkpoints using exact compact reference cases and replayable old-key neighborhood gate metrics

## Next Blocker

m347-old-key-neighborhood-alpha-sweep-run
