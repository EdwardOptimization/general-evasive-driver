# m3217-wp1-belief-substitution-bounded-iteration Research Review

## Summary

- Generated at UTC: 20260611T152330Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: wp1_terminal_fail_bounded_iteration_leak_gate_stop_c2_bound_accepted
- Decision reason: Completed: the single pre-registered WP1 bounded iteration (M3216 all-arms-fail route) ran through the harness with the design frozen ex ante in wp1_iter1_prereg.json (50/50 closed-loop mixing by the frozen M3216 best-selection seekers with mu-free dv jitter, heteroscedastic 3-member ensembles, confidence-gated continuous injection sigma_max 0.12 with internal-detector fallback, fresh 20270301-based streams, criteria unchanged); the rerun mixed-set leak gate FAILED in all 4 cells (pooled decision-frame single-frame->mu linear OOF R^2 0.399/0.336/0.436/0.234, MLP 0.329/0.325/0.457/-0.046 vs bar 0.1) while every scripted half passes (linear -0.080..+0.047) and every closed-loop half is massively current-frame mu-readable (linear 0.632-0.967): the seeker's approach state at the reveal encodes its own detector belief, so distribution-matched on-policy training data is inherently incompatible with the attribution gate on this construction; the run stopped before any training/selection/validation episode per the frozen terminal route, consuming the single iteration: WP1 primary FAIL is accepted as the C2 bound (belief learnable to R^2 0.91-0.99 at estimator level, M3216 delay12 +0.185 lo97.5 +0.110 the only standing substitution positive, but not redeemable through this interface at the 50 percent recapture bar), G-B does not open WP2 and the paper scope contracts to C1 + estimator positive + bound; auxiliary measurement only with the engineering incumbent unchanged and no validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Hypothesis

The SINGLE pre-registered bounded excitation/representation iteration granted by the M3216 all-arms-fail route -- 50/50 mixing of closed-loop floor-seeker trajectories into the leak-gated training data (repair A, distribution shift) plus confidence-gated continuous per-tick belief injection with internal-detector fallback (repair B, injection timing), on UNCHANGED criteria, construction, floor/oracle definitions, and two-way statistics with fresh re-based seed streams -- can decide the WP1 terminal verdict (primary: L3_GRU recaptures at least 50 percent of the re-measured matched prize in at least 3 of the 4 frozen eligible cells with one-sided 97.5 percent lower bounds excluding 0; PASS opens G-B/WP2, FAIL is accepted as the C2 bound with no further iteration) before any validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/research-plan-phase2-capability-boundary-tracking.md
- parent_dataset: runs/feasibility_audit/wp1_full/summary.json, runs/feasibility_audit/wp0_degraded_sweep/summary.json
- parent_config: experiments/feasibility_audit/wp1_iter1_prereg.json, experiments/feasibility_audit/wp1_prereg.json
- parent_objective: close Phase-2 WP1 terminally: execute the one bounded iteration of the all-arms-fail route and accept its outcome as the G-B adjudication (PASS -> WP2; FAIL -> the C2 learnable-but-not-redeemable bound)
- derived_from: docs/m3216-wp1-modular-belief-experiment.md, docs/m3215-wp0-degraded-sweep-bridge-validation.md, experiments/feasibility_audit/wp1_prereg.json, scripts/feasibility_audit/wp1_full_run.py, scripts/feasibility_audit/wp1_data_pipeline.py, scripts/feasibility_audit/wp1_estimator_trainer.py
- blocked_by: G-B (WP2 sequence-proposal + verifier work) requires this milestone's terminal primary verdict
- supersedes: any further WP1 substitution iteration: the M3216 route grants exactly one bounded iteration and this milestone consumes it
- invalidates: none

## Success Criteria

- runs/feasibility_audit/wp1_iter1_full/summary.json exists with status completed (or the pre-registered terminal stopped_dataset_leak_gate_failed_iter1 stop), both prereg echoes, per-cell paired tables with confidence telemetry, the M3216 comparison block, and a deterministic terminal verdict
- every gated readout consumed the fresh 20270301-based subst_val stream only, with floor, oracle, and all injected arms on identical episode sets per cell
- the mixed-set leak gate results (pooled + per-subset probes) are recorded per cell before any training
- docs/m3217-wp1-belief-substitution-bounded-iteration.md records the frozen iteration design, the measured per-cell recapture table against the M3216 reference, the terminal adjudication, and the G-B routing
- ActiveSafetyReflexDriver, public driver defaults, and the engineering mainline objective boundary are unchanged

## Failure Criteria

- summary.json missing, status neither completed nor the pre-registered terminal leak-gate stop, or any required verdict non-deterministic
- criteria, seeds, cells, injection constants, or construction constants altered after the full run started
- any gated arm measured on fewer than 240 validation episodes in a cell
- a second iteration attempted, or results quoted as driver-performance, robustness, gate-validity, feasibility-proof, paper, or self-ID evidence
- the milestone trains, promotes, or mutates any driving policy

## Evidence Gates

- M3217 must freeze the full iteration design (mix ratio, closed-loop collection policies and dv jitter, re-based seed streams, heteroscedastic ensemble representation, continuous-injection rule with SIGMA_MAX 0.12 and STALE_MAX 50, fallback semantics, scope cuts, compute budget) in experiments/feasibility_audit/wp1_iter1_prereg.json BEFORE the --full run and echo it into summary.json
- M3217 must keep every gated criterion of experiments/feasibility_audit/wp1_prereg.json unchanged: primary rule (L3_GRU, recapture >= 0.5, >= 3 of 4 cells, one-sided 97.5% lower bound > 0, two-way SE), floor/oracle definitions, 240-episode paired validation budget, 8 training seeds, construction constants
- M3217 must rerun the dataset leak gate on the NEW MIXED set per cell (decision-frame single-frame -> mu linear AND MLP out-of-fold R^2 <= 0.1, pooled standard subset) and stop before training on any failure; the stop is terminal
- M3217 must draw selection AND validation episodes from fresh re-based seed streams (base 20270301, layout unchanged) because every M3216 subst_val outcome was read by the diagnosis that produced this design
- M3217 must accept the outcome as the WP1 terminal verdict either way: PASS -> G-B opens WP2; FAIL (including a leak-gate stop) -> the C2 bound is accepted and the paper scope contracts to C1 + the estimator-level positive + the bound; no second iteration
- M3217 must keep the L0_frame current-frame leak control riding under the identical continuous interface with its unchanged >= 3-cell route
- M3217 must leave ActiveSafetyReflexDriver, public driver defaults, and the engineering mainline objective boundary unchanged (RampPolicyController gains an inert-by-default injection_mode parameter; bit-compat asserted by the existing hook tests)

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not weaken thresholds, extend seeds, re-pick cells, or change construction constants after the --full run starts
- do not tune SIGMA_MAX, STALE_MAX, the mix ratio, or any estimator hyperparameter on validation outcomes (all frozen ex ante in wp1_iter1_prereg.json)
- do not reuse any 20270101-based M3216 substitution episode for selection or validation
- do not run a second iteration on FAIL, and do not reinterpret a leak-gate stop as anything but a terminal FAIL bound
- do not give estimator arms any eval-time freedom beyond the frozen best-selection seeker config + the frozen injection constants
- do not read any number as driver-performance, robustness, feasibility-proof, gate-validity, paper, or self-ID evidence
- do not promote, mutate, or train any driving policy inside M3217 (supervised mu estimators only)
- do not bypass make_env_from_config when constructing degraded envs

## Failure Taxonomy

- metric_artifact
- seed_fragility
- contract_violation
- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m3217-wp1-belief-substitution-bounded-iteration
- type: infrastructure
- checkpoint: runs/feasibility_audit/wp1_iter1_full/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wp1_terminal_fail_bounded_iteration_leak_gate_stop_c2_bound_accepted
- reason: Completed: the single pre-registered WP1 bounded iteration (M3216 all-arms-fail route) ran through the harness with the design frozen ex ante in wp1_iter1_prereg.json (50/50 closed-loop mixing by the frozen M3216 best-selection seekers with mu-free dv jitter, heteroscedastic 3-member ensembles, confidence-gated continuous injection sigma_max 0.12 with internal-detector fallback, fresh 20270301-based streams, criteria unchanged); the rerun mixed-set leak gate FAILED in all 4 cells (pooled decision-frame single-frame->mu linear OOF R^2 0.399/0.336/0.436/0.234, MLP 0.329/0.325/0.457/-0.046 vs bar 0.1) while every scripted half passes (linear -0.080..+0.047) and every closed-loop half is massively current-frame mu-readable (linear 0.632-0.967): the seeker's approach state at the reveal encodes its own detector belief, so distribution-matched on-policy training data is inherently incompatible with the attribution gate on this construction; the run stopped before any training/selection/validation episode per the frozen terminal route, consuming the single iteration: WP1 primary FAIL is accepted as the C2 bound (belief learnable to R^2 0.91-0.99 at estimator level, M3216 delay12 +0.185 lo97.5 +0.110 the only standing substitution positive, but not redeemable through this interface at the 50 percent recapture bar), G-B does not open WP2 and the paper scope contracts to C1 + estimator positive + bound; auxiliary measurement only with the engineering incumbent unchanged and no validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Next Blocker

m3217-wp1-belief-substitution-bounded-iteration
