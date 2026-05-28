# m1275-paper-route-fidelity-fault-source-synthesis Research Review

## Summary

- Generated at UTC: 20260528T125722Z
- Type: gate
- Gate tier: process
- Promotion decision: fidelity_fault_source_synthesis_promote_to_source_intervention_materialization
- Decision reason: M1275 synthesizes M1265-M1274 four-wheel source evidence as source-positive corpus infrastructure and opens the source-intervention materialization branch

## Hypothesis

The fidelity fault source branch has enough evidence for branch-level synthesis before any further source experiment.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1265-paper-route-fidelity-fault-source-design.md, docs/m1266-paper-route-four-wheel-fault-dynamics-pilot.md, docs/m1267-paper-route-four-wheel-fault-source-integration-design.md, docs/m1268-paper-route-four-wheel-fault-source-shape-smoke.md, docs/m1269-paper-route-four-wheel-fault-source-shape-result-audit.md, docs/m1270-paper-route-four-wheel-source-viability-calibration-design.md, docs/m1271-paper-route-four-wheel-source-viability-calibration-smoke.md, docs/m1272-paper-route-four-wheel-source-viability-calibration-result-audit.md, docs/m1273-paper-route-four-wheel-source-corpus-export.md, docs/m1274-paper-route-four-wheel-source-corpus-export-result-audit.md, runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json, runs/m1273_four_wheel_source_corpus_export/summary.json
- parent_config: experiments/manifests/m1265-paper-route-fidelity-fault-source-design.json, experiments/manifests/m1274-paper-route-four-wheel-source-corpus-export-result-audit.json
- parent_objective: synthesize fidelity fault source branch evidence after four-wheel source-positive corpus export
- derived_from: m1265-paper-route-fidelity-fault-source-design, m1274-paper-route-four-wheel-source-corpus-export-result-audit
- blocked_by: M1274 routes to branch synthesis because the fidelity fault source branch reached synthesis cadence
- supersedes: another narrow four-wheel source experiment before synthesis
- invalidates: None

## Success Criteria

- docs/m1275-paper-route-fidelity-fault-source-synthesis.md exists
- synthesis summarizes M1265-M1274 evidence
- synthesis records supported and falsified claims
- synthesis classifies failure taxonomy
- synthesis assesses public-gate overfit risk
- synthesis chooses next branch decision
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- synthesis is missing
- synthesis ignores M1274 cadence route
- synthesis admits another narrow source run without a branch decision
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1275 must preserve actor input contract
- M1275 must not train controllers
- M1275 must not run PPO
- M1275 must not use private holdout
- M1275 must not promote a checkpoint
- M1275 must summarize M1265-M1274 evidence
- M1275 must choose continue, pivot, stop, or promote_to_next_branch

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote a checkpoint
- do not add hidden parameters, fault labels, per-wheel forces, oracle outcomes, or search outputs to actor inputs
- do not lower capability-separable thresholds
- do not start another source run before synthesis
- do not claim compact four-wheel source as high-fidelity validation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1275-paper-route-fidelity-fault-source-synthesis
- type: gate
- checkpoint: docs/m1275-paper-route-fidelity-fault-source-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fidelity_fault_source_synthesis_promote_to_source_intervention_materialization
- reason: M1275 synthesizes M1265-M1274 four-wheel source evidence as source-positive corpus infrastructure and opens the source-intervention materialization branch

## Next Blocker

m1276-paper-route-four-wheel-source-intervention-materialization-design
