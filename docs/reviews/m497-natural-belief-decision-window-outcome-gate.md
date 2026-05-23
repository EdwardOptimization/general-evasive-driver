# m497-natural-belief-decision-window-outcome-gate Research Review

## Summary

- Generated at UTC: 20260523T235014Z
- Type: gate
- Gate tier: proof
- Promotion decision: natural_decision_window_gate_reject_wrong_history_event_proof_admit_m498_no_effect_audit
- Decision reason: M497 classifies control_only_sensitivity: wrong-history has 15 margin-only proof rows and 0 event rows while reset/zero-current controls have 472 proof rows and 17 event rows

## Hypothesis

Early decision-window wrong-history interventions on the M496 targeted natural belief surface can reveal whether pre-reveal command-response belief affects outcomes before current-response correction dominates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m496_natural_belief_targeted_pair_triage/summary.json, runs/m496_natural_belief_targeted_pair_triage/targeted_pairs.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m496-natural-belief-targeted-pair-triage.json
- parent_objective: natural decision-window wrong-history outcome gate
- derived_from: m496-natural-belief-targeted-pair-triage
- blocked_by: m496-natural-belief-targeted-pair-triage
- supersedes: None
- invalidates: None

## Success Criteria

- outcome gate runs complete for both configs
- combined summary reports wrong_tail_once proof and event rows
- combined summary reports reset_tail and zero_current_tail controls
- result is classified as positive proof, no-effect, or control-only sensitivity
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- either config gate fails to run
- too many pairs are invalid because requested snapshots are missing
- summary cannot separate wrong-history from reset/zero-current controls
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- split M496 targeted pairs by config
- run decision-window wrong-history outcome gates on both M494 configs
- use early offsets 0 2 4 8 around the matched decision point
- report wrong-history proof rows, event rows, reset controls, zero-current controls, label/seed/target/config diversity
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not count aggregate behavior smoke as self-ID proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m497-natural-belief-decision-window-outcome-gate
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: natural_decision_window_gate_reject_wrong_history_event_proof_admit_m498_no_effect_audit
- reason: M497 classifies control_only_sensitivity: wrong-history has 15 margin-only proof rows and 0 event rows while reset/zero-current controls have 472 proof rows and 17 event rows

## Next Blocker

pending M497 natural belief decision-window outcome gate
