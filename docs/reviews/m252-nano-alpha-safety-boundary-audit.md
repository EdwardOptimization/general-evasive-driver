# m252-nano-alpha-safety-boundary-audit Research Review

## Summary

- Generated at UTC: 20260522T150111Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m253_full_public_gate_for_a0_00008
- Decision reason: M252 maps the nano alpha cliff: exact source losses improve monotonically while M183/M170 replay passes through alpha 0.00008 and fails at 0.00009 on row16

## Hypothesis

The proof-retention cliff between alpha 0.00005 and 0.0001 can be mapped with the fixed interpolation sweep, allowing the project to choose the largest safe source-calibrated alpha or prove that M250 is already the safe boundary.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt, runs/m249_protected_key_source_actor_coupling_probe/optimized_checkpoint.pt, runs/m250_nano_custom_m239_to_protected_source_interpolation/checkpoints/alpha_0_00005.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
- parent_config: src/autodrift/checkpoint_interpolation.py, docs/m250-protected-key-source-actor-coupling-calibration.md, docs/m251-checkpoint-interpolation-alpha-token-fix.md
- parent_objective: source-aware exact objective improvement, M183 M170 near-boundary replay retention
- derived_from: m250-protected-key-source-actor-coupling-calibration, m251-checkpoint-interpolation-alpha-token-fix
- blocked_by: m251-checkpoint-interpolation-alpha-token-fix
- supersedes: None
- invalidates: None

## Success Criteria

- generate collision-free interpolation checkpoints for alphas around 0.00005 to 0.0001
- evaluate exact source-aware M232 loss for each alpha
- run M183 M170 replay gate for candidate alphas
- identify the largest alpha that improves exact source losses and preserves M183 M170 replay retention
- no PPO is run

## Failure Criteria

- all alphas above M250 fail M183 M170 replay retention
- exact source loss stops improving before any replay-safe alpha
- a collision or label ambiguity remains in interpolation outputs
- change the actor input contract

## Evidence Gates

- fixed interpolation sweep between alpha 0.00005 and 0.0001
- M245 exact source-aware objective gate
- M183 M170 replay gate
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M252
- do not use the discarded colliding M250 micro sweep
- do not promote any alpha that loses M183 M170 normal success
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m252-nano-alpha-safety-boundary-audit
- type: driver_candidate
- checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m253_full_public_gate_for_a0_00008
- reason: M252 maps the nano alpha cliff: exact source losses improve monotonically while M183/M170 replay passes through alpha 0.00008 and fails at 0.00009 on row16

## Next Blocker

Run full public proof and behavior gates for m252_a0_00008 before any PPO.
