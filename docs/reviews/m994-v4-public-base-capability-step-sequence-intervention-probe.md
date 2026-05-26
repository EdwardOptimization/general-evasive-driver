# m994-v4-public-base-capability-step-sequence-intervention-probe Research Review

## Summary

- Generated at UTC: 20260526T141908Z
- Type: gate
- Gate tier: generalization
- Promotion decision: sequence_temporal_history_positive_route_to_audit
- Decision reason: M994 finds 277 temporal accepted rows across 9 fault pairs and 17 seeds but 0 cross-fault accepted rows so route to claim-scope audit

## Hypothesis

Sequence-level command-response mismatch over M991 reset-only rows will create stronger and more behaviorally grounded belief-mismatch evidence than a single wrong hidden-state swap.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m993-v4-public-base-capability-step-sequence-intervention-design.md, runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv
- parent_config: configs/m991_capability_step_fault_source_wave.json, experiments/manifests/m993-v4-public-base-capability-step-sequence-intervention-design.json
- parent_objective: implement and run a no-training sequence-level action-response mismatch probe for capability-step reset-only rows
- derived_from: m993-v4-public-base-capability-step-sequence-intervention-design, m992-v4-public-base-capability-step-reset-only-audit
- blocked_by: M993 requires a trace-window probe before sequence-level interventions can be evaluated
- supersedes: None
- invalidates: None

## Success Criteria

- probe runner exists or an implementation blocker is documented
- summary.json exists if the probe runs
- source rows are reconstructed from M991 reset-only diagnostics
- normal rows and intervention rows are reported separately
- sequence action gaps and terminal margin gaps are reported
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false

## Failure Criteria

- hidden event labels enter actor observations
- actor parameters change
- training or PPO starts
- promotion occurs
- reset-only rows are counted as sequence wrong-history proof
- route decision is missing

## Evidence Gates

- M994 must not run PPO
- M994 must not promote
- M994 must not change actor inputs
- M994 must preserve hidden fault labels as metadata only
- M994 must report reset-only, action-only, and outcome-critical sequence rows separately

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize actor parameters
- do not use private holdout
- do not claim true per-wheel/asymmetric faults
- do not count reset-only rows as accepted sequence wrong-history rows
- do not proceed to PPO

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m994-v4-public-base-capability-step-sequence-intervention-probe
- type: gate
- checkpoint: runs/m994_v4_public_base_capability_step_sequence_intervention_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: sequence_temporal_history_positive_route_to_audit
- reason: M994 finds 277 temporal accepted rows across 9 fault pairs and 17 seeds but 0 cross-fault accepted rows so route to claim-scope audit

## Next Blocker

m995-v4-public-base-capability-step-temporal-history-audit
