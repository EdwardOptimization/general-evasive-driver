# m1268-paper-route-four-wheel-fault-source-shape-smoke Research Review

## Summary

- Generated at UTC: 20260528T122538Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M1268 passes as infrastructure if it emits source-shape artifacts, strict accepted-row counts, and guardrails without training, PPO, promotion, or actor-input expansion.

## Hypothesis

The four-wheel fault dynamics pilot can produce strict capability-separable source rows in a no-policy source-shape smoke while preserving clean actor observations.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1267-paper-route-four-wheel-fault-source-integration-design.md, src/autodrift/four_wheel_dynamics.py
- parent_config: experiments/manifests/m1267-paper-route-four-wheel-fault-source-integration-design.json
- parent_objective: implement no-policy four-wheel fault source-shape smoke
- derived_from: m1267-paper-route-four-wheel-fault-source-integration-design
- blocked_by: M1267 admits no-policy source-shape smoke before Gym/actor integration
- supersedes: direct actor training or PPO on unvalidated four-wheel source
- invalidates: None

## Success Criteria

- runs/m1268_four_wheel_fault_source_shape_smoke/summary.json exists
- scenario_summary.csv exists
- snapshot_candidates.csv exists
- action_lattice.csv exists
- action_rollouts.csv exists
- matched_capability_pairs.csv exists
- accepted_separable_pairs.csv exists
- collision-dominance diagnostics are reported
- actor_input_contract_changed == false
- labels_enter_actor_input == false
- training_started == false
- ppo_used == false
- promoted == false
- private_holdout_used == false
- accepted_thresholds_relaxed == false

## Failure Criteria

- run artifacts are missing
- observation mapping includes per-wheel/fault metadata
- accepted thresholds are lowered
- training or PPO starts
- promotion occurs
- high-fidelity validation is claimed

## Evidence Gates

- M1268 must preserve actor input contract
- M1268 must not train controllers
- M1268 must not run PPO
- M1268 must not use private holdout
- M1268 must not promote
- M1268 must report accepted-source rows and collision-dominance diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel/fault labels to actor inputs
- do not lower accepted-source thresholds
- do not claim high-fidelity validation from the compact pilot
- do not use policy success as a substitute for strict source acceptance

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1269-paper-route-four-wheel-fault-source-shape-result-audit
