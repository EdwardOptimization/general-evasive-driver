# m1266-paper-route-four-wheel-fault-dynamics-pilot Research Review

## Summary

- Generated at UTC: 20260528T121505Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1266 passes as infrastructure if the four-wheel fault primitives are finite, deterministic, and express signed asymmetric-fault yaw response without changing actor inputs.

## Hypothesis

A compact source-only four-wheel model can express finite signed yaw-moment differences under left-right/per-wheel faults, enabling a later source-collector integration branch.

## Lineage

- parent_checkpoint: None
- parent_dataset: docs/m1265-paper-route-fidelity-fault-source-design.md
- parent_config: experiments/manifests/m1265-paper-route-fidelity-fault-source-design.json
- parent_objective: implement a bounded source-only four-wheel fault dynamics pilot
- derived_from: m1265-paper-route-fidelity-fault-source-design
- blocked_by: M1265 admits a source-only four-wheel/fault dynamics pilot
- supersedes: another current single-track proxy-fault source repair
- invalidates: None

## Success Criteria

- src/autodrift/four_wheel_dynamics.py exists
- tests/test_four_wheel_dynamics.py exists
- docs/m1266-paper-route-four-wheel-fault-dynamics-pilot.md exists
- nominal finite rollout test passes
- left-right split-mu signed yaw-moment test passes
- single-wheel brake-pull signed yaw-moment test passes
- single-wheel grip-collapse capacity test passes
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- model or tests are missing
- bounded faults produce non-finite state or force outputs
- asymmetric faults cannot produce signed yaw-moment differences
- actor input contract is expanded
- training, PPO, private holdout, promotion, or threshold relaxation occurs

## Evidence Gates

- M1266 must preserve actor input contract
- M1266 must not train controllers
- M1266 must not run PPO
- M1266 must not use private holdout
- M1266 must not promote
- M1266 must not integrate new privileged observations into actor inputs
- M1266 must not claim high-fidelity simulator or real-vehicle validity

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel or fault labels to actor inputs
- do not lower capability-separable thresholds
- do not replace the main Gym env without a separate design
- do not claim source-positive rows from model-unit tests

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1267-paper-route-four-wheel-fault-source-integration-design
