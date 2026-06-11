# m3215-wp0-degraded-sweep-bridge-validation Research Review

## Summary

- Generated at UTC: 20260611T123228Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: ga_fail_family_specific_scope_bridge_falsified_route_wp1_family1
- Decision reason: Completed: pre-registered WP0.2/WP0.3 closing sweep measured 20 cells (2 families x 10 degradation cells, 120 validation episodes/arm/cell, Wilson+Newcombe CIs, 32832 task episodes, 18.3 min) through the harness; family-2 clean replication PASSES (VoI_matched +0.025 <= 0.05) but only 2/5 NEW family-2 cells reach VoI_matched >= 0.15 (ar1 r0.9 +0.167, ar1 r0.95 +0.292; dropout +0.025, eprand -0.125, piecewise -0.067) so the pre-registered G-A verdict is law_not_replicated_family_specific_scope with WP1 routed to family #1 only; family-1 anchors all revive at the matched anchor (delay5 +0.333, delay12 +0.458, delay25 +0.183, noise +0.150, CIs excluding 0); the noise-buys-delay bridge is FALSIFIED as pre-registered (pooled agreement 0.40 < 0.75, Spearman -0.21 < 0.6; AR(1) saturates detection latency yet flips VoI in opposite directions on the two families) and is demoted to direct per-cell measurement; auxiliary measurement only with the engineering incumbent unchanged and no validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Hypothesis

A pre-registered degraded-regime sweep over the extended M3214 wrapper modes (AR(1) correlated noise, frame dropout, episode-random and piecewise time-varying delay, at least five new cells per family plus the existing delay/noise anchors) on both the B2K2 tight-window family and the frozen F2C1 family with matched-anchor VoI against the best belief-free floor at 12 mu points x at least 10 validation seeds with Wilson CIs can decide the G-A gate (two-regime-law replication on family 2) and the falsifiable noise-buys-delay bridge (threshold-classification agreement at least 75 percent and Spearman at least 0.6) before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/research-plan-phase2-capability-boundary-tracking.md
- parent_dataset: experiments/feasibility_audit/family2_spec.json, experiments/feasibility_audit/degraded_regime_final.json, experiments/feasibility_audit/slip_onset_detectability.json
- parent_config: experiments/feasibility_audit/wp0_degraded_sweep_prereg.json
- parent_objective: close Phase-2 WP0: replicate or refute the two-regime law direction on family 2 under hardened statistics and validate the detection-latency bridge across the new degradation modes
- derived_from: docs/research-plan-phase2-capability-boundary-tracking.md, experiments/feasibility_audit/family2_spec.json, experiments/feasibility_audit/degraded_regime_final.json, docs/m3214-selfid-degradation-pipeline-integration-g1-ignition-gate.md
- blocked_by: WP1 eligible-cell freezing requires the WP0.3 hardened re-measurement delivered by this milestone, the G-A gate must be adjudicated before WP1 runs on family 2
- supersedes: reading the 2-seed degraded_regime_final cell estimates as main-table numbers
- invalidates: none

## Success Criteria

- runs/feasibility_audit/wp0_degraded_sweep/summary.json exists with status completed, the pre-registration echo, per-cell results for both families with n_val_episodes_per_arm >= 120, Wilson CIs, and deterministic ga_gate and bridge verdicts
- every degradation cell ran through make_env_from_config with the identical wrapper construction path including the clean cell
- the bridge table reports delta_L, predicted and measured VoI, classification agreement, and Spearman over the pooled new cells
- docs/m3215-wp0-degraded-sweep-bridge-validation.md records the pre-registered criteria, the measured tables, the G-A adjudication, and the routing
- ActiveSafetyReflexDriver, public driver defaults, and the engineering mainline objective boundary are unchanged

## Failure Criteria

- summary.json missing, status not completed, or any required verdict non-deterministic
- criteria, seeds, or cells altered after the full run started
- any validation arm below 120 episodes in a non-dropped cell
- results quoted as driver-performance, robustness, gate-validity, feasibility-proof, paper, or self-ID evidence
- the milestone trains, promotes, or mutates any driver or checkpoint

## Evidence Gates

- M3215 must freeze all decision criteria (cells, seeds, VoI definition, G-A rule, bridge rule, saturation rule, budget rule) in experiments/feasibility_audit/wp0_degraded_sweep_prereg.json before the --full run and echo them into summary.json
- M3215 must measure every validation arm on at least 120 episodes per cell (12 mu points x at least 10 disjoint validation seeds) with Wilson 95% CIs; if runtime exceeds budget, cells are dropped and reported, seeds are never reduced
- M3215 must use the matched anchor (same-cell degraded oracle) against the best belief-free floor (max over seeker variants with per-cell re-calibrated detectors and fixed plans) as the primary VoI readout
- M3215 must use the drive-side (throttle) seek style in the family-2 seeker grid per the frozen family-2 design lesson
- M3215 must report the bridge verdict in whichever direction it lands, including AR(1) breaking the prediction
- M3215 must leave ActiveSafetyReflexDriver, public driver defaults, and the engineering mainline objective boundary unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not weaken thresholds, extend seeds, or re-pick cells after seeing results
- do not substitute the clean-anchor VoI for the matched-anchor VoI in the G-A or bridge verdicts
- do not tune the seeker on validation seeds; selection and validation streams stay disjoint
- do not read any cell number as driver-performance, robustness, feasibility-proof, gate-validity, paper, or self-ID evidence
- do not promote, mutate, or train any driver or checkpoint inside M3215
- do not bypass make_env_from_config when constructing degraded envs

## Failure Taxonomy

- metric_artifact
- seed_fragility
- contract_violation
- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m3215-wp0-degraded-sweep-bridge-validation
- type: infrastructure
- checkpoint: runs/feasibility_audit/wp0_degraded_sweep/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: ga_fail_family_specific_scope_bridge_falsified_route_wp1_family1
- reason: Completed: pre-registered WP0.2/WP0.3 closing sweep measured 20 cells (2 families x 10 degradation cells, 120 validation episodes/arm/cell, Wilson+Newcombe CIs, 32832 task episodes, 18.3 min) through the harness; family-2 clean replication PASSES (VoI_matched +0.025 <= 0.05) but only 2/5 NEW family-2 cells reach VoI_matched >= 0.15 (ar1 r0.9 +0.167, ar1 r0.95 +0.292; dropout +0.025, eprand -0.125, piecewise -0.067) so the pre-registered G-A verdict is law_not_replicated_family_specific_scope with WP1 routed to family #1 only; family-1 anchors all revive at the matched anchor (delay5 +0.333, delay12 +0.458, delay25 +0.183, noise +0.150, CIs excluding 0); the noise-buys-delay bridge is FALSIFIED as pre-registered (pooled agreement 0.40 < 0.75, Spearman -0.21 < 0.6; AR(1) saturates detection latency yet flips VoI in opposite directions on the two families) and is demoted to direct per-cell measurement; auxiliary measurement only with the engineering incumbent unchanged and no validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Next Blocker

m3215-wp0-degraded-sweep-bridge-validation
