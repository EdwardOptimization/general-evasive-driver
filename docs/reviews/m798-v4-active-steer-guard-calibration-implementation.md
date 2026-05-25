# m798-v4-active-steer-guard-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260525T044357Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_active_steer_guard_low_margin_corpus_blocked
- Decision reason: M798 implements the active steer guard corpus gate and correctly blocks before training because current low-margin rows are 12 variants of one source only

## Hypothesis

A lexicographic active/source-diverse steer guard can convert M795's collision-free strong-gap near miss into a safer diagnostic candidate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m797-v4-active-steer-guard-calibration-design.md, docs/m796-v4-steer-attributed-residual-calibration-audit.md, runs/m795_v4_steer_attributed_residual_calibration/summary.json, runs/m795_v4_steer_attributed_residual_calibration/alpha_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/gate_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/component_gate_metrics.csv, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m797-v4-active-steer-guard-calibration-design.json
- parent_objective: implement no-PPO active-steer guard calibration diagnostic
- derived_from: m797-v4-active-steer-guard-calibration-design
- blocked_by: m797-v4-active-steer-guard-calibration-design
- supersedes: None
- invalidates: None

## Success Criteria

- M798 writes run artifacts and docs
- M798 confirms actor and residual head checksums unchanged
- M798 trains only calibrator parameters
- M798 reports separability metrics and low-margin guard rows
- M798 classifies the result with the M797 taxonomy

## Failure Criteria

- implementation trains actor or residual parameters
- implementation runs PPO
- implementation promotes a checkpoint
- implementation omits separability or source-diverse low-margin metrics
- implementation weakens comparison thresholds

## Evidence Gates

- M798 implements active-steer guard calibration only
- M798 freezes base actor and M761 residual head
- M798 trains only the small steer/brake calibrator
- M798 runs separability and low-margin guard checks before closed-loop candidate claims
- M798 blocks PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train the base actor
- do not train the M761 residual head
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not weaken M786 or M780 thresholds
- do not tune only the single public active source
- do not skip separability or source-diverse low-margin checks

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m798-v4-active-steer-guard-calibration-implementation
- type: infrastructure
- checkpoint: runs/m798_v4_active_steer_guard_calibration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_active_steer_guard_low_margin_corpus_blocked
- reason: M798 implements the active steer guard corpus gate and correctly blocks before training because current low-margin rows are 12 variants of one source only

## Next Blocker

m799-v4-active-steer-guard-calibration-audit
