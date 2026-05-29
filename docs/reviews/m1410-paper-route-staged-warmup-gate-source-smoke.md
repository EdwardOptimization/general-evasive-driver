# m1410-paper-route-staged-warmup-gate-source-smoke Research Review

## Summary

- Generated at UTC: 20260529T004454Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: staged_warmup_gate_source_structural_pass_route_to_result_audit
- Decision reason: M1410 structurally passes with 1690 source rows 298 matched/bucketed rows 31 matched/bucketed seeds and warmup command-response evidence but high gate collision diagnostics require audit before outcome probing

## Hypothesis

The staged warmup gate API can materialize source-diverse matched/bucketed reveal rows with measurable warmup command-response evidence without actor-input changes.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1409-paper-route-warmup-reveal-pressure-branch-synthesis.md, docs/m1408-paper-route-staged-obstacle-warmup-api-implementation.md
- parent_config: experiments/manifests/m1409-paper-route-warmup-reveal-pressure-branch-synthesis.json
- parent_objective: create staged warmup gate configs, add source smoke warmup diagnostics, and run no-training source smoke
- derived_from: m1409-paper-route-warmup-reveal-pressure-branch-synthesis
- blocked_by: M1409 synthesis continues the branch only to staged warmup gate source smoke
- supersedes: running figure-eight-only source smoke again, running outcome interventions before staged warmup source viability is known
- invalidates: None

## Success Criteria

- staged warmup source-smoke configs exist
- runs/m1410_staged_warmup_gate_source_smoke/summary.json exists
- matching, source-diversity, and warmup gate diagnostic metrics are reported
- result chooses next route without outcome intervention, training, PPO, promotion, private holdout, training corpus export, or actor-input expansion

## Failure Criteria

- source smoke artifact is missing
- warmup gate diagnostics are missing
- matching or source-diversity metrics are missing
- result routes directly to training or claim expansion

## Evidence Gates

- M1410 must run no-training source smoke for staged warmup gate before outcome interventions
- M1410 must report source diversity and matched/bucketed current rows
- M1410 must report warmup gate diagnostics and warmup command-response evidence metrics
- M1410 must not run outcome interventions, train, run PPO, promote, use private holdout, export a training corpus, or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not add actor oracle labels
- do not claim self-identification from source materialization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1410-paper-route-staged-warmup-gate-source-smoke
- type: infrastructure
- checkpoint: runs/m1410_staged_warmup_gate_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: staged_warmup_gate_source_structural_pass_route_to_result_audit
- reason: M1410 structurally passes with 1690 source rows 298 matched/bucketed rows 31 matched/bucketed seeds and warmup command-response evidence but high gate collision diagnostics require audit before outcome probing

## Next Blocker

m1411-paper-route-staged-warmup-gate-source-result-audit
