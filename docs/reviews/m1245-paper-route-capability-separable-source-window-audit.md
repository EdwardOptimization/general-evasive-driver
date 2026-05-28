# m1245-paper-route-capability-separable-source-window-audit Research Review

## Summary

- Generated at UTC: 20260528T093802Z
- Type: gate
- Gate tier: process
- Promotion decision: source_window_audit_select_viability_band_relocation_smoke
- Decision reason: M1245 audits M1244 as close-obstacle but viability-band-missing source-negative result and selects bounded near-boundary relocation smoke

## Hypothesis

Repeated low-regret source-negative results can be classified by auditing source-window and boundary-conditioning variables before changing simulator fidelity or training an actor.

## Lineage

- parent_checkpoint: none
- parent_dataset: runs/m1244_capability_separable_short_sequence_lattice_smoke/summary.json, runs/m1244_capability_separable_short_sequence_lattice_smoke/matched_capability_pairs.csv, runs/m1244_capability_separable_short_sequence_lattice_smoke/sequence_rollouts.csv
- parent_config: experiments/manifests/m1244-paper-route-capability-separable-short-sequence-lattice-smoke.json
- parent_objective: audit whether source-window and boundary-conditioning choices explain repeated low-regret source-negative results
- derived_from: m1244-paper-route-capability-separable-short-sequence-lattice-smoke
- blocked_by: M1244 short-sequence lattice infrastructure passed but accepted_separable_pairs == 0
- supersedes: more short-sequence template tuning before source-window audit
- invalidates: assuming a short sequence lattice alone is sufficient to expose hidden-dynamics separability

## Success Criteria

- docs/m1245-paper-route-capability-separable-source-window-audit.md exists
- M1244 summary metrics are quoted
- best-action divergence and cross-regret distributions are inspected
- source-window and boundary-conditioning hypotheses are evaluated
- one bounded next step is selected
- private holdout remains unused
- no training, PPO, promotion, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1245 starts training or PPO
- M1245 treats zero accepted separable pairs as source-positive
- M1245 changes actor inputs
- M1245 leaves the next route vague

## Evidence Gates

- M1245 may audit M1244 artifacts only
- M1245 must not train controllers
- M1245 must not run PPO
- M1245 must not use private holdout
- M1245 must not promote
- M1245 must preserve actor input contract
- M1245 must select one bounded next source-window repair or explicitly route to simulator-fidelity design

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters or oracle labels to actor inputs
- do not claim self-identification from source construction
- do not continue tuning sequence templates without source-window diagnosis

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1245-paper-route-capability-separable-source-window-audit
- type: gate
- checkpoint: docs/m1245-paper-route-capability-separable-source-window-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_window_audit_select_viability_band_relocation_smoke
- reason: M1245 audits M1244 as close-obstacle but viability-band-missing source-negative result and selects bounded near-boundary relocation smoke

## Next Blocker

m1246-paper-route-capability-separable-viability-band-relocation-smoke
