# m233-protected-key-aware-ppo-smoke-from-m224 Research Review

## Summary

- Generated at UTC: 20260522T132357Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_ppo_smoke_replay_and_protected_key_failure
- Decision reason: M233 retains behavior but fixed losses do not improve M183 M170 replay drops to 16/17 and protected key fails at normal margin 0.204645; keep M224 and audit closed-loop retention

## Hypothesis

Using the combined M223/M231 snippet anchor during PPO should preserve the replay proof surface and the historical protected key better than M229, which anchored only M223 snippets.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.csv
- parent_config: configs/ppo_m229_snippet_anchor_from_m224_smoke.json
- parent_objective: rollout-state M224 baseline action anchor, combined M223/M231 preferred-only snippet action anchor, combined M223/M231 outcome intervention auxiliary loss
- derived_from: m232-protected-key-combined-snippet-anchor-corpus
- blocked_by: m229-snippet-anchored-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- run exactly one 1024-step PPO smoke from M224 with the M232 combined corpus
- improve or at least not regress the fixed objective against M224 within the existing smoke tolerance
- retain M183/M193/M212/M223 replay drops
- retain behavior seed success at the M224 level
- pass protected key 9944 within the existing normal-margin window

## Failure Criteria

- protected key 9944 fails
- any old or current replay gate loses normal-history success retention
- behavior seed success regresses materially
- PPO is lengthened or repeated before the one-smoke result is audited
- actor input contract changes

## Evidence Gates

- fixed M223/M232 objective evaluation
- M183 replay gates
- M193 replay gate
- M212 replay gate
- M223 replay gate
- behavior seeds 9505 and 9506
- protected key 9944 guard
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change actor inputs
- do not loosen replay or protected-key thresholds
- do not lengthen PPO before this one-smoke gate passes
- do not promote if protected key fails even when fixed loss improves

## Failure Taxonomy

- proof_washout
- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m233-protected-key-aware-ppo-smoke-from-m224
- type: driver_candidate
- checkpoint: runs/ppo_m233_protected_key_combined_anchor_from_m224_seed5220/checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844014
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: reject_ppo_smoke_replay_and_protected_key_failure
- reason: M233 retains behavior but fixed losses do not improve M183 M170 replay drops to 16/17 and protected key fails at normal margin 0.204645; keep M224 and audit closed-loop retention

## Next Blocker

Audit why first-action snippet anchoring did not preserve closed-loop replay and protected-key margins before any more PPO.
