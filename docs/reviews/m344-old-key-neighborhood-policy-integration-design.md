# m344-old-key-neighborhood-policy-integration-design Research Review

## Summary

- Generated at UTC: 20260523T093926Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m345_old_key_neighborhood_replay_gate_adapter
- Decision reason: M344 defines the old-key neighborhood gate as first-class proof gate but requires a replayable candidate adapter before future PPO candidates can replace singleton 9944 veto dominance

## Hypothesis

The M343 old-key neighborhood gate can become the first-class old-key acceptance gate, with singleton 9944 retained as a diagnostic row instead of a standalone PPO-continuation veto.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- parent_dataset: runs/m343_old_key_neighborhood_gate_probe/summary.json, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
- parent_config: experiments/manifests/m343-old-key-neighborhood-gate-probe.json, docs/m343-old-key-neighborhood-gate-probe.md
- parent_objective: replace singleton old-key floor dominance with a source-diverse old-key neighborhood gate
- derived_from: m343-old-key-neighborhood-gate-probe
- blocked_by: m343-old-key-neighborhood-gate-probe
- supersedes: None
- invalidates: None

## Success Criteria

- document a concrete gate order for future PPO continuation
- separate neighborhood distribution failure from singleton diagnostic warning
- state promotion and no-promotion rules for candidates that pass neighborhood gate but warn on 9944
- update roadmap/status/scoreboard with the next executable PPO or gate milestone
- research validation passes

## Failure Criteria

- policy lets candidates hide 9944 diagnostics
- policy allows promotion from old-key neighborhood pass alone
- policy treats the M341 public corpus as private holdout evidence
- policy changes actor input contract
- policy starts PPO before gate order is documented

## Evidence Gates

- design acceptance-stack order using old-key neighborhood gate
- define how singleton 9944 remains diagnostic without single-row veto dominance
- define when neighborhood pass plus singleton warning may advance to full public gate
- define when neighborhood failure blocks PPO or promotion
- do not run PPO or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not remove 9944 visibility
- do not lower old-key neighborhood thresholds
- do not use public old-key rows as private holdout evidence
- do not change actor inputs
- do not train or repair a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m344-old-key-neighborhood-policy-integration-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m345_old_key_neighborhood_replay_gate_adapter
- reason: M344 defines the old-key neighborhood gate as first-class proof gate but requires a replayable candidate adapter before future PPO candidates can replace singleton 9944 veto dominance

## Next Blocker

m345-old-key-neighborhood-replay-gate-adapter
