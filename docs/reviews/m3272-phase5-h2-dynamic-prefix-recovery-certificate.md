# m3272-phase5-h2-dynamic-prefix-recovery-certificate Research Review

## Summary

- Generated at UTC: 20260710T103325Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: h2_quick_no_strict_witness
- Decision reason: 4/5 continuously reached branches were eligible and all 150 rows plus 10/10 replays passed health gates; zero-steer throttle or brake matched the expanded optimum at every eligible branch with 0.00 s steering advantage; full blocked

## Hypothesis

Branching the unchanged M3271 nested recovery-policy libraries from continuously simulated states along the hash-frozen M3266 Chrono slide-entry prefix can remove direct-reset tire-state inconsistency and produce robust strict finite-horizon recovery witnesses, defined by baseline failure or at least 0.20 s earlier recovery with added countersteer.

## Lineage

- parent_checkpoint: docs/m3266-phase5-g0b-slide-mode-onset-pricing.md, docs/m3270-phase5-h0-fixed-library-overlap-certificate.md, docs/m3271-phase5-h1-postslip-nested-recovery-certificate.md, docs/preslip-reachable-set-dual-proof-theory-2026-07.md
- parent_dataset: experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json, experiments/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate_quick.json
- parent_config: scripts/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.py, scripts/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate.py, scripts/feasibility_audit/phase5_h2_dynamic_prefix_recovery_certificate.py
- parent_objective: test strict post-slip recovery expansion from dynamically consistent tire states, preserve corrected physical actions and exact control-set nesting from M3271
- derived_from: M3266 same-plant prefix has 72-frame slide dwell and exact replay, M3271 direct reset matched body beta but rear slip was only 0.00136 rad, a recovery-time gap of at least 0.20 s defines a nonempty deadline interval with strict finite-horizon set membership
- blocked_by: only prefix states passing frozen beta dwell rear-slip and four-wheel truth are eligible
- supersedes: direct body-state injection as the source of post-slip branch states
- invalidates: resetting wheel or tire relaxation state at a recovery branch, using ineligible prefix times as already-sliding evidence, overriding M3271's negative reset-state finding

## Success Criteria

- preregistration freezes source prefix hash branch grid unchanged policy library and seed streams
- quick has at least three eligible branches and one strict witness
- managed resumable full completes 1080 candidate rows and 24 exact winner replays
- all action nesting prefix branch telemetry finite-observation and weak-inclusion gates pass
- at least eight cells are eligible and three cells strict on all three seeds across two branch groups
- source-prefix simultaneous pedals and finite signed scope remain explicit

## Failure Criteria

- full runs before passing quick
- branch states are reset or differ between policies
- ineligible tire states are counted
- a time gap below 0.20 s is called strict
- strict support is claimed without robust matched witnesses

## Evidence Gates

- freeze M3266 source artifact and physical-segment hashes before quick/full
- run the common prefix without resetting at the recovery branch
- freeze branch grid unchanged M3271 policy library thresholds and disjoint seeds
- require final four prefix frames beta at least 0.20 and branch rear slip at least 0.15
- require identical prefix and branch hashes across every policy
- keep the six baseline policies as a strict subset of the 30-policy expanded set
- require ten stable frames with forward speed at least 4 m/s
- require baseline failure or at least 0.20 s recovery-time advantage with steering actually used
- require exact winner replay and full negative reporting
- scope support to one signed finite prefix branch and policy family

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reset body wheel or tire states at the branch
- do not change source prefix branch times policies thresholds seeds or eligibility after results
- do not use normalized pedal zero as physical zero
- do not call uniform braking ESC
- do not count ineligible branch times in strict evidence
- do not hide source-prefix simultaneous pedal segments baseline recoveries or active failures
- do not mutate ActiveSafetyReflexDriver or train a policy
- do not claim all post-slip states policies vehicles real cars promotion or self-ID

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m3272-phase5-h2-dynamic-prefix-recovery-certificate
- type: infrastructure
- checkpoint: None
- success_rate: 0
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: h2_quick_no_strict_witness
- reason: 4/5 continuously reached branches were eligible and all 150 rows plus 10/10 replays passed health gates; zero-steer throttle or brake matched the expanded optimum at every eligible branch with 0.00 s steering advantage; full blocked

## Next Blocker

None recorded.
