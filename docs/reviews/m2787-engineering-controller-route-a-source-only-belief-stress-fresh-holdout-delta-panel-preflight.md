# m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight Research Review

## Summary

- Generated at UTC: 20260605T124847Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: route_to_source_only_belief_stress_fresh_holdout_delta_panel_result_audit
- Decision reason: M2787 fresh-holdout paired source-only delta panel status_pass true required artifacts present seed indices 4 5 6 7 disjoint from M2784 0 1 2 3 horizon 120 greater than 80 wrote 144 paired execution rows 72 paired delta rows 13 proof gates 8 generalization holdout gates 4 promotion guards 7 actor guards 8 mitigation guards 11 claim rows and 25 gates all pass candidate-minus-source road margin positive 72/72 yaw-rate lower 60/72 obstacle-clearance mixed 43 positive 29 negative final speed positive 63/72 throttle/brake conflict unchanged actor 72/action 3 no hidden oracle mitigation rows outside denominators rejects validation ranking promotion success-rate verdict performance paper current-sim high-fidelity full ideal driver and self-ID claims routes to M2788 audit

## Hypothesis

A fresh-holdout paired source-only closed-loop delta panel can test whether the small M2784 candidate-vs-source diagnostic shifts persist on unseen seed indices while preserving actor and claim boundaries.

## Lineage

- parent_checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt, runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoints/m2782_belief_stress_short_training_candidate.pt
- parent_dataset: docs/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.md, docs/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit.md, runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/summary.json, runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/paired_delta_rows.csv, runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/summary.json, runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/checkpoint_manifest.json
- parent_config: experiments/manifests/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.json, experiments/manifests/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit.json, experiments/manifests/m2784-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-preflight.json, experiments/manifests/m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight.json
- parent_objective: run a fresh-holdout source-only paired closed-loop diagnostic delta panel for M2655 source and M2782 candidate after M2786 synthesis rejects direct promotion
- derived_from: m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis, m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit, m2784-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-preflight, m2782-engineering-controller-route-a-source-only-belief-stress-short-training-continuation-preflight
- blocked_by: M2784 paired deltas are small and source-only, so they require unseen-seed holdout before interpretation, M2784 obstacle-clearance deltas are mixed and cannot support promotion, M2786 rejects another same-surface audit or no-new-data reanalysis, M2638 high-fidelity source dependency remains unresolved and cannot be bypassed
- supersedes: direct checkpoint promotion from M2784 paired deltas, same-seed M2784 paired delta reanalysis as the next main action, road-margin-only interpretation of the M2782 candidate checkpoint
- invalidates: None

## Success Criteria

- runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/summary.json exists
- docs/m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight.md exists
- M2787 consumes M2786 M2785 M2784 M2782 and M2655 artifacts only
- M2787 writes paired execution rows paired delta rows proof retention gates generalization holdout gates promotion guards actor guards mitigation guards claim rows gate matrix run-state and M2788 audit manifest
- M2787 uses fresh holdout seed indices outside M2784 seed_index 0..3
- M2787 preserves P0 observation 72 action 3 no hidden/oracle actor input and actor-invisible labels
- M2787 keeps mitigation reference rows outside ordinary denominators
- M2787 writes no validation ranking promotion performance paper current-sim high-fidelity full ideal driver or self-ID claim

## Failure Criteria

- M2787 changes actor input or action contract
- M2787 exposes role dynamics stress curriculum admission outcome route progress success or verdict labels to actor input
- M2787 uses mitigation reference rows as ordinary successes
- M2787 shrinks to a single seed
- M2787 repeats only M2784 seed_index 0..3
- M2787 ranks source/candidate checkpoints selects a winner promotes a checkpoint or computes success-rate verdicts
- M2787 claims repair success driver performance validation readiness/result high-fidelity validation paper finite-window-vs-GRU current-sim verdict full ideal driver completion or self-ID result

## Evidence Gates

- M2787 must run a paired source-only closed-loop diagnostic panel over M2655 source and M2782 candidate checkpoints after M2786 synthesis
- M2787 must use fresh holdout seed indices outside the M2784 seed_index 0..3 surface
- M2787 must cover all ordinary role families dynamics axes and belief-stress families without cherry-picking positive M2784 rows
- M2787 must preserve actor P0 observation shape 72 action shape 3 no hidden/oracle actor input and no actor-visible role dynamics stress curriculum admission outcome success progress route or verdict labels
- M2787 must write paired execution rows paired delta rows proof retention gates generalization holdout gates promotion guards actor guards mitigation guards claim rows gate matrix summary doc run-state and M2788 audit manifest
- M2787 must keep mitigation reference rows outside ordinary denominators
- M2787 must reject validation ranking winner promotion success-rate verdict driver-performance paper current-sim high-fidelity full ideal driver and self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not expose role labels dynamics labels intervention labels stress labels curriculum labels admission labels outcome labels success labels progress labels route labels or verdict labels to actor input
- do not train or run PPO
- do not use mitigation reference rows as ordinary successes
- do not shrink to a single seed
- do not cherry-pick only M2784-positive road-margin rows
- do not tune one public proof row and compare as a discovery
- do not rank source and candidate checkpoints
- do not select a winner
- do not promote a checkpoint
- do not compute success-rate or controller-family verdict metrics
- do not execute measured validation
- do not import external simulator dependencies
- do not run external simulation
- do not claim repair success
- do not claim validation readiness
- do not claim validation result
- do not claim driver performance
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim current-sim verdict
- do not claim high-fidelity validation
- do not claim full ideal driver completion
- do not claim level3 self-identification

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout

## Scoreboard

- milestone: m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight
- type: infrastructure
- checkpoint: runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_source_only_belief_stress_fresh_holdout_delta_panel_result_audit
- reason: M2787 fresh-holdout paired source-only delta panel status_pass true required artifacts present seed indices 4 5 6 7 disjoint from M2784 0 1 2 3 horizon 120 greater than 80 wrote 144 paired execution rows 72 paired delta rows 13 proof gates 8 generalization holdout gates 4 promotion guards 7 actor guards 8 mitigation guards 11 claim rows and 25 gates all pass candidate-minus-source road margin positive 72/72 yaw-rate lower 60/72 obstacle-clearance mixed 43 positive 29 negative final speed positive 63/72 throttle/brake conflict unchanged actor 72/action 3 no hidden oracle mitigation rows outside denominators rejects validation ranking promotion success-rate verdict performance paper current-sim high-fidelity full ideal driver and self-ID claims routes to M2788 audit

## Next Blocker

None recorded.
