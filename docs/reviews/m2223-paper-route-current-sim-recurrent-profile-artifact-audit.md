# m2223-paper-route-current-sim-recurrent-profile-artifact-audit Research Review

## Summary

- Generated at UTC: 20260601T124834Z
- Type: gate
- Gate tier: process
- Promotion decision: current_sim_recurrent_profile_artifact_audit_route_to_checkpoint_quality_audit
- Decision reason: M2223 finds L3 profile/provenance/alias/hidden reset routing structurally clean but L3 checkpoint smoke-scale weak route to checkpoint-quality audit no rerun ranking paper FW-vs-GRU or self-ID claims

## Hypothesis

Existing profile materialization, config, and readiness artifacts can determine whether L3 zero-success/reset equivalence is a config/provenance/evaluation issue before any rerun.

## Lineage

- parent_checkpoint: not_applicable_artifact_audit
- parent_dataset: docs/m2222-paper-route-current-sim-profile-history-failure-diagnosis-result-audit.md, runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/summary.json, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json, runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv, runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/summary.json, runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/profile_checkpoint_join_rows.csv, configs/paper_route_profiles/m1190_l3_online_gru_smoke.json, configs/paper_route_profiles/m1190_l3_reset_control_smoke.json, src/autodrift/controller_profiles.py
- parent_config: experiments/manifests/m2222-paper-route-current-sim-profile-history-failure-diagnosis-result-audit.json
- parent_objective: audit L3 online/reset recurrent-profile artifacts before repair, rerun, ranking, or conclusion
- derived_from: m2222-paper-route-current-sim-profile-history-failure-diagnosis-result-audit
- blocked_by: M2221 confirms L3 online/reset zero-success and reset equivalence
- supersedes: direct recurrent profile repair without artifact audit, direct finite-window-vs-GRU conclusion from M2221
- invalidates: None

## Success Criteria

- docs/m2223-paper-route-current-sim-recurrent-profile-artifact-audit.md exists
- audit checks L3 online/reset profile configs, checkpoint provenance, reset-control semantics, and recurrent hidden-state handling from artifacts/code
- next route is explicit
- no reset rollout measured execution training ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- audit document is missing
- audit cannot locate required L3 artifacts
- audit overclaims M2221 as ranking or finite-window-vs-GRU evidence
- new rollout or ranking is performed

## Evidence Gates

- M2223 must audit L3 online/reset profile config and checkpoint provenance
- M2223 must check reset-control alias/correction semantics
- M2223 must check recurrent/hidden-state evaluation semantics from artifacts/code only
- M2223 must decide config repair, checkpoint/training audit, recurrent evaluation harness repair, bounded negative synthesis, or stop
- M2223 must not run reset, rollout, measured execution, policy action, training, replay, or PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit driver behavior
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not rank controller families
- do not select a winner
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification

## Failure Taxonomy

- behavior_regression
- lineage_invalid
- metric_artifact

## Scoreboard

- milestone: m2223-paper-route-current-sim-recurrent-profile-artifact-audit
- type: gate
- checkpoint: docs/m2223-paper-route-current-sim-recurrent-profile-artifact-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_sim_recurrent_profile_artifact_audit_route_to_checkpoint_quality_audit
- reason: M2223 finds L3 profile/provenance/alias/hidden reset routing structurally clean but L3 checkpoint smoke-scale weak route to checkpoint-quality audit no rerun ranking paper FW-vs-GRU or self-ID claims

## Next Blocker

m2223-paper-route-current-sim-recurrent-profile-artifact-audit
