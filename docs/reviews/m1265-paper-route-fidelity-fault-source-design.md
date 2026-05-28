# m1265-paper-route-fidelity-fault-source-design Research Review

## Summary

- Generated at UTC: 20260528T120946Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1265 passes if it defines the next fidelity-source branch with bounded implementation/scout criteria and no training or threshold relaxation.

## Hypothesis

A source-fidelity design can identify a bounded next branch that is more likely to produce true capability-separable rows than more current-model proxy-fault repair.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1264-paper-route-richer-fault-capability-source-synthesis.md, runs/m1259_richer_fault_capability_source_smoke/summary.json, runs/m1262_richer_fault_regret_boundary_retarget_smoke/summary.json
- parent_config: experiments/manifests/m1264-paper-route-richer-fault-capability-source-synthesis.json
- parent_objective: design the next source-fidelity branch after current single-track/proxy-fault source mining remains zero-accepted
- derived_from: m1264-paper-route-richer-fault-capability-source-synthesis
- blocked_by: M1264 pivots from current-model richer proxy faults to fidelity fault source design
- supersedes: another current-model proxy-fault repair without a source-fidelity design
- invalidates: None

## Success Criteria

- docs/m1265-paper-route-fidelity-fault-source-design.md exists
- design explains why current single-track/proxy source is insufficient
- design separates minimum in-repo four-wheel/fault pilot from external high-fidelity simulator validation
- design defines source acceptance gates and guardrails
- design pre-registers the next bounded implementation or scout if admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design proposes another current-model proxy-only run without a new fidelity variable
- design lowers strict accepted-source thresholds
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1265 must preserve actor input contract
- M1265 must not train controllers
- M1265 must not run PPO
- M1265 must not use private holdout
- M1265 must not promote
- M1265 must define the minimum next source-fidelity branch before implementation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, fault labels, oracle outcomes, or search outputs to actor inputs
- do not lower capability-separable thresholds
- do not claim current single-track proxies are true single-wheel or per-wheel faults
- do not choose an external simulator without a bounded integration/validation plan

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1266-paper-route-four-wheel-fault-dynamics-pilot
