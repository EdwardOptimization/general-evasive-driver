# m1591-paper-route-history-pairability-source-generation-branch-synthesis Research Review

## Summary

- Generated at UTC: 20260529T162829Z
- Type: gate
- Gate tier: process
- Promotion decision: history_pairability_source_generation_synthesis_continue_to_one_bounded_clean_source_implementation
- Decision reason: M1591 synthesizes M1581-M1590 and admits exactly one bounded clean-source implementation before mandatory audit

## Hypothesis

After M1590, the pairability-first source-generation branch has enough positive and negative evidence to require synthesis before any further implementation milestone.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1582_history_pairability_source_miner_smoke/summary.json, runs/m1585_source_diverse_pairability_history_intervention_smoke/summary.json, runs/m1588_history_vs_control_active_set_selector/summary.json, runs/m1588_history_vs_control_active_set_selector/clean_directed_pair_rows.csv, docs/m1590-paper-route-clean-history-control-source-generation-repair-design.md
- parent_config: experiments/manifests/m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair.json, experiments/manifests/m1590-paper-route-clean-history-control-source-generation-repair-design.json
- parent_objective: synthesize pairability-first source generation after clean history-control source repair design
- derived_from: m1580-paper-route-recoverable-active-set-generation-branch-synthesis-after-high-speed-late-repair, m1590-paper-route-clean-history-control-source-generation-repair-design
- blocked_by: workflow synthesis cadence reached after M1590, M1588 clean surface exists but clean_directed_pair_count is 7 below target 8, M1585 intervention rows were source-diverse but control-dominated
- supersedes: direct M1591 clean-source implementation without synthesis, another broad pairability source miner, another broad intervention smoke without clean selector target, candidate materialization after M1588
- invalidates: None

## Success Criteria

- docs/m1591-paper-route-history-pairability-source-generation-branch-synthesis.md exists
- synthesis summarizes M1581-M1590 evidence
- supported and unsupported claims are explicit
- failure taxonomy summary is explicit
- public-gate overfit risk is explicit
- next branch decision is explicit
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked

## Failure Criteria

- synthesis document is missing
- synthesis treats broad pairability or control-dominated rows as level3 self-ID evidence
- synthesis ignores M1588 clean-count shortfall or high-speed caveat
- synthesis routes directly to training PPO promotion private holdout corpus export actor-input changes or candidate materialization

## Evidence Gates

- M1591 must synthesize M1581-M1590 pairability-first branch evidence
- M1591 must separate broad pairability, intervention plumbing, clean selector evidence, and paper-level self-ID claims
- M1591 must summarize clean-positive and dominated/control-only evidence
- M1591 must assess public-gate overfit risk after repeated public-row repairs
- M1591 must choose continue, pivot, stop, or promote_to_next_branch
- M1591 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run history interventions
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not relax clean selector thresholds
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1591-paper-route-history-pairability-source-generation-branch-synthesis
- type: gate
- checkpoint: docs/m1591-paper-route-history-pairability-source-generation-branch-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: history_pairability_source_generation_synthesis_continue_to_one_bounded_clean_source_implementation
- reason: M1591 synthesizes M1581-M1590 and admits exactly one bounded clean-source implementation before mandatory audit

## Next Blocker

m1592-paper-route-clean-history-control-source-generation-repair-implementation
