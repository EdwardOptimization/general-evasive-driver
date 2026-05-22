# m268-m267-guarded-actor-update-from-m264 Research Review

## Summary

- Generated at UTC: 20260522T172845Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_actor_update_proof_washout
- Decision reason: M268 improves sampled and exact M267 loss but fails old M183 M168 M183 M170 and M193 M189 replay gates so behavior and protected-key gates were not run

## Hypothesis

A tiny preferred-only actor-coupling update from M264 on the M267 protected-surface corpus may improve the refreshed protected-surface objective without washing out old replay surfaces, the new M267 surface, behavior, or the old protected-key diagnostic.

## Lineage

- parent_checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m267-protected-surface-objective-replay-conversion.json, docs/m267-protected-surface-objective-replay-conversion.md
- parent_objective: tiny preferred-only actor-coupling update on the refreshed current-family protected surface
- derived_from: m267-protected-surface-objective-replay-conversion
- blocked_by: m267-protected-surface-objective-replay-conversion
- supersedes: None
- invalidates: None

## Success Criteria

- start from runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- use runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz
- run exactly one small actor update before any repeat or PPO
- use the M216/M224-style small recipe with actor_coupling and preferred-only snippet action anchor
- improve fixed M267 objective versus M264 on independent fixed-batch eval
- preserve all listed public replay gates
- preserve behavior seeds 9505 and 9506
- preserve old protected key diagnostic
- actor input contract remains unchanged

## Failure Criteria

- run PPO before the actor update is gated
- drop any old or refreshed replay row
- lose behavior retention or protected-key diagnostic
- fixed objective improves but proof surfaces regress
- change actor observation inputs

## Evidence Gates

- M267 M264 fixed objective eval
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

- do not run PPO in M268
- do not run multiple actor-update seeds before the first seed passes
- do not promote based only on fixed objective improvement
- do not change actor inputs
- do not delete or loosen the old protected key diagnostic

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m268-m267-guarded-actor-update-from-m264
- type: driver_candidate
- checkpoint: runs/m268_m264_actor_coupling_m267_snippet_pref_anchor100_s10_lr5e5_seed10073/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_actor_update_proof_washout
- reason: M268 improves sampled and exact M267 loss but fails old M183 M168 M183 M170 and M193 M189 replay gates so behavior and protected-key gates were not run

## Next Blocker

m269-m268-old-surface-proof-washout-audit
