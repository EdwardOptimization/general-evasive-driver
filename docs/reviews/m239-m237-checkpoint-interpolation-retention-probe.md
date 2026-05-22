# m239-m237-checkpoint-interpolation-retention-probe Research Review

## Summary

- Generated at UTC: 20260522T135315Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: promote_m239_a500_public_gate_base
- Decision reason: M239 alpha 0.5 is the largest tested interpolation that passes full replay protected key and behavior gates while retaining fixed objective improvement; use as public-gate base and repeat fresh seed

## Hypothesis

If M237 failed mainly because the PPO update was too large for near-boundary proof windows, a smaller interpolation from M224 toward M237 should preserve M183 M170 and protected key while retaining some fixed-objective improvement. If no useful alpha passes, the next repair needs a stronger on-policy margin-retention objective rather than more action anchoring.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt, runs/ppo_m237_trajectory_anchor_from_m224_seed5221/checkpoint.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m237_m183_m170_replay_gate_seed9510/boundary_replay_rows.csv, runs/m237_critical_key_seed9944/guard_results.csv
- parent_config: configs/ppo_m237_trajectory_anchor_from_m224_smoke.json
- parent_objective: no-PPO checkpoint interpolation trust-region probe, fixed M232/M223 objective retention, M183 M170 and protected-key proof retention
- derived_from: m238-trajectory-anchor-retention-failure-audit
- blocked_by: m237-trajectory-anchored-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- generate a bounded interpolation sweep from M224 to M237 without PPO
- evaluate fixed M232/M223 losses for all alphas
- evaluate M183 M170 replay and protected key for candidate alphas
- promote only if an alpha passes proof gates and improves or does not materially regress fixed objective
- run behavior seeds only after proof gates identify a promotable alpha

## Failure Criteria

- run PPO
- select alpha using private holdout
- promote an alpha that fails M183 M170 replay
- promote an alpha that fails protected key
- change the actor input contract

## Evidence Gates

- checkpoint interpolation sweep
- fixed M232/M223 objective evaluation
- M183 M170 replay gate
- protected key 9944 guard
- M183 M168 replay gate for selected alpha
- M193 replay gate for selected alpha
- M212 replay gate for selected alpha
- M223 replay gate for selected alpha
- behavior seeds 9505 and 9506 if any alpha passes proof gates
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M239
- do not loosen replay or protected-key thresholds
- do not promote an alpha that fails M183 M170 or protected key
- do not use private holdout to select alpha
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m239-m237-checkpoint-interpolation-retention-probe
- type: driver_candidate
- checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844117
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m239_a500_public_gate_base
- reason: M239 alpha 0.5 is the largest tested interpolation that passes full replay protected key and behavior gates while retaining fixed objective improvement; use as public-gate base and repeat fresh seed

## Next Blocker

Repeat the trajectory-anchored PPO recipe on a fresh seed and require interpolation-guarded promotion before accepting a new base.
