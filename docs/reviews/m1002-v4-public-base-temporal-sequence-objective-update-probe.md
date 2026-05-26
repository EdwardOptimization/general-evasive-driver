# m1002-v4-public-base-temporal-sequence-objective-update-probe Research Review

## Summary

- Generated at UTC: 20260526T162627Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_sequence_update_exact_candidate_route_to_public_replay_gate_design
- Decision reason: M1002 produces 5 exact actor_mean-only candidates best alpha 0.2 with non-actor parameters unchanged and routes to public replay gate design

## Hypothesis

A small actor_mean-only update over the M997 temporal objective can produce an exact-gate-passing candidate without PPO or promotion.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m1001-v4-public-base-temporal-sequence-objective-update-design.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json
- parent_config: experiments/manifests/m1001-v4-public-base-temporal-sequence-objective-update-design.json
- parent_objective: run exact-gated actor_mean-only temporal sequence objective update probe
- derived_from: m1001-v4-public-base-temporal-sequence-objective-update-design, m1000-v4-public-base-temporal-sequence-objective-evaluator
- blocked_by: M1001 admits only a tiny exact objective-only actor_mean update probe
- supersedes: None
- invalidates: running PPO or replay gates before exact candidate selection

## Success Criteria

- probe command completes
- summary.json exists
- only actor_mean changes
- candidate exact gates are evaluated
- ppo_used == false
- promoted == false

## Failure Criteria

- non-actor_mean parameters change
- training metrics are non-finite
- diagnostic cross-fault rows are positive targets
- PPO starts
- promotion occurs

## Evidence Gates

- M1002 must not run PPO
- M1002 must not promote
- M1002 must update only actor_mean
- M1002 must select candidates only by exact objective gates
- M1002 must not use diagnostic cross-fault rows as positives

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not update GRU or encoders
- do not use private holdout
- do not claim cross-fault wrong-history self-ID
- do not train variant histories toward degraded actions
- do not proceed to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1002-v4-public-base-temporal-sequence-objective-update-probe
- type: infrastructure
- checkpoint: runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_update_exact_candidate_route_to_public_replay_gate_design
- reason: M1002 produces 5 exact actor_mean-only candidates best alpha 0.2 with non-actor parameters unchanged and routes to public replay gate design

## Next Blocker

m1003-v4-public-base-temporal-sequence-update-public-replay-gate-design
