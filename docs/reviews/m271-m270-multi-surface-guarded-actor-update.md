# m271-m270-multi-surface-guarded-actor-update Research Review

## Summary

- Generated at UTC: 20260522T174315Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_multi_surface_actor_update_proof_washout
- Decision reason: M271 improves sampled and exact M270 loss but fails M183 M193 M212 and M223 replay gates so behavior and protected-key gates were not run

## Hypothesis

A small actor-coupling update from M264 using the M270 source-balanced multi-surface corpus can improve the combined objective while retaining old M183/M193 and current M267 proof surfaces.

## Lineage

- parent_checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.csv
- parent_config: experiments/manifests/m270-source-balanced-multi-surface-anchor-corpus.json, docs/m270-source-balanced-multi-surface-anchor-corpus.md
- parent_objective: source-balanced multi-surface outcome/snippet anchor update
- derived_from: m270-source-balanced-multi-surface-anchor-corpus
- blocked_by: m270-source-balanced-multi-surface-anchor-corpus
- supersedes: None
- invalidates: None

## Success Criteria

- start from runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- use runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- run exactly one small actor update before any repeat or PPO
- improve fixed M270 objective versus M264 on independent fixed-batch eval
- preserve all listed public replay gates
- preserve behavior seeds 9505 and 9506
- preserve old protected key diagnostic
- actor input contract remains unchanged

## Failure Criteria

- run PPO before the actor update is gated
- drop any old or refreshed replay row
- lose behavior retention or protected-key diagnostic
- combined objective improves but proof surfaces regress
- change actor observation inputs

## Evidence Gates

- M270 combined fixed objective eval
- M183 M168 and M170 replay retention
- M193 M189 replay retention
- M212 M204 replay retention
- M223 M219 replay retention
- M267 M264 replay retention
- old protected key 9944 diagnostic replay
- behavior seeds 9505 and 9506

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M271
- do not run multiple actor-update seeds before the first seed passes
- do not promote based only on combined objective improvement
- do not change actor inputs
- do not delete or loosen the old protected key diagnostic

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m271-m270-multi-surface-guarded-actor-update
- type: driver_candidate
- checkpoint: runs/m271_m264_actor_coupling_m270_multisurface_anchor100_s10_lr5e5_seed10074/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_multi_surface_actor_update_proof_washout
- reason: M271 improves sampled and exact M270 loss but fails M183 M193 M212 and M223 replay gates so behavior and protected-key gates were not run

## Next Blocker

m272-m271-interpolation-retention-probe
