# m1267-paper-route-four-wheel-fault-source-integration-design Research Review

## Summary

- Generated at UTC: 20260528T121758Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1267 passes if it designs deterministic four-wheel source integration with clean actor observations and unchanged accepted-source thresholds.

## Hypothesis

A bounded integration design can route four-wheel fault primitives into source mining while keeping deployable actor observations clean.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1266-paper-route-four-wheel-fault-dynamics-pilot.md
- parent_config: experiments/manifests/m1266-paper-route-four-wheel-fault-dynamics-pilot.json
- parent_objective: design integration of four-wheel fault primitives into source collection and capability-separable evaluation
- derived_from: m1266-paper-route-four-wheel-fault-dynamics-pilot
- blocked_by: M1266 implements four-wheel fault primitives but does not integrate them into source mining
- supersedes: direct source mining before integration guardrails are designed
- invalidates: None

## Success Criteria

- docs/m1267-paper-route-four-wheel-fault-source-integration-design.md exists
- design defines source snapshot schema
- design defines observation mapping from four-wheel state to human-view frame
- design defines metadata boundaries for per-wheel/fault data
- design pre-registers the next bounded implementation if admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design requires per-wheel/fault labels in actor input
- design lowers strict accepted-source thresholds
- design skips deterministic reconstruction requirements
- training, PPO, private holdout, promotion, or threshold relaxation occurs

## Evidence Gates

- M1267 must preserve actor input contract
- M1267 must not train controllers
- M1267 must not run PPO
- M1267 must not use private holdout
- M1267 must not promote
- M1267 must design source integration before implementation

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
- do not run source mining before source reconstruction and observation mapping are specified

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1268-paper-route-four-wheel-fault-source-shape-smoke
