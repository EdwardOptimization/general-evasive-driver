# m827-v4-wrong-cross-fault-history-intervention-design Research Review

## Summary

- Generated at UTC: 20260525T105157Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: wrong_cross_fault_history_intervention_design_admit_m828
- Decision reason: M827 designs current-geometry replay with matched different-fault hidden/history injection and source-diverse wrong-history gates while keeping PPO and promotion blocked

## Hypothesis

A real wrong-cross-fault history intervention can provide stronger evidence for response-history self-identification than zero-command or reset-hidden ablations.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/history_intervention_rows.csv, docs/m826-v4-extreme-hidden-dynamics-data-route-audit.md
- parent_config: experiments/manifests/m826-v4-extreme-hidden-dynamics-data-route-audit.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design real wrong-cross-fault hidden/history injection before more source expansion or PPO
- derived_from: m826-v4-extreme-hidden-dynamics-data-route-audit
- blocked_by: M825 only logged wrong_cross_fault_history as unsupported and positives were dominated by zero-command sensitivity
- supersedes: None
- invalidates: None

## Success Criteria

- M827 writes a design document for paired wrong-history injection
- M827 specifies exact required artifacts for implementation
- M827 specifies pass/fail gates for normal versus wrong-history margin and action degradation
- M827 preserves the P0 human-view actor contract
- M827 keeps PPO and promotion blocked

## Failure Criteria

- M827 proposes hidden fault labels as actor inputs
- M827 treats diagnostic matched pairs as sufficient proof without intervention replay
- M827 admits PPO before wrong-history evidence exists
- M827 relaxes M825 sparse gates after seeing results

## Evidence Gates

- M827 must design wrong-cross-fault history injection without adding hidden fault labels to actor input
- M827 must define matched-pair source selection and rejection rules
- M827 must define replay semantics for current geometry with injected wrong hidden/history
- M827 must define margin/action gates that separate response-history self-ID from zero-command sensitivity
- M827 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not feed fault labels or hidden params to actor
- do not claim wrong-history sensitivity from matched action divergence alone
- do not use zero-command-only rows as proof of response-history self-ID
- do not claim true wheel-level physical faults from current proxies

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m827-v4-wrong-cross-fault-history-intervention-design
- type: infrastructure
- checkpoint: docs/m827-v4-wrong-cross-fault-history-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_cross_fault_history_intervention_design_admit_m828
- reason: M827 designs current-geometry replay with matched different-fault hidden/history injection and source-diverse wrong-history gates while keeping PPO and promotion blocked

## Next Blocker

wrong-cross-fault history injection is not yet implemented
