# m3271-phase5-h1-postslip-nested-recovery-certificate Research Review

## Summary

- Generated at UTC: 20260710T101507Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: h1_quick_inconclusive
- Decision reason: 60/60 rows action nesting and weak inclusion passed with 4/4 exact replays; reset rear slip was 0.00136 rad below the 0.15 slide-truth threshold; neither mirrored cell was strict and full was blocked

## Hypothesis

On a frozen finite panel of already-sliding Chrono/TMeasy states, an expanded control library that exactly contains a zero-steer physical-pedal baseline and adds countersteer feedback can strictly enlarge the finite-horizon recovery set under correct physical pedal semantics, matched initial-state hashes, tire truth, speed-preserving recovery, and exact replay.

## Lineage

- parent_checkpoint: docs/preslip-reachable-set-dual-proof-theory-2026-07.md, docs/m3266-phase5-g0b-slide-mode-onset-pricing.md, docs/m3270-phase5-h0-fixed-library-overlap-certificate.md, docs/current-status.md
- parent_dataset: experiments/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.json, experiments/feasibility_audit/phase5_h0_fixed_library_overlap_certificate.json
- parent_config: scripts/feasibility_audit/phase5_g0_preslip_reachability_proof_pricing.py, scripts/feasibility_audit/phase5_g0b_slide_mode_onset_pricing.py, scripts/feasibility_audit/phase5_h1_postslip_nested_recovery_certificate.py
- parent_objective: test the strict post-slip half of the two-regime proposition, replace invalid normalized-pedal recovery audits with correct physical semantics
- derived_from: M3266 proves same-plant slide entry from beta zero with 72-frame dwell and exact replay, M3270 satisfies the registered finite pre-slip numerical gate, nested control sets imply weak recovery-set inclusion and a matched witness can establish strictness
- blocked_by: universal post-slip recovery and real-vehicle claims remain outside this finite panel
- supersedes: scripts/audits/chrono_recovery.py recovery counts, scripts/audits/recovery_reachability.py recovery counts
- invalidates: calling uniform braking ESC, treating normalized pedal zero as physical zero, claiming strictness without a matched baseline-fail expanded-success witness

## Success Criteria

- preregistration freezes 18 full cells 30 policies and seed streams before quick/full
- both mirrored quick cells are healthy strict witnesses
- managed resumable full completes 1620 candidate rows and 36 exact winner replays
- all state-match nesting tire-truth finite-observation and weak-inclusion gates pass
- at least six cells are strict on all three seeds spanning both signs and two beta tiers
- old invalid audit counts and finite claim scope remain explicit

## Failure Criteria

- full runs before passing quick
- physical and normalized pedal semantics are conflated
- baseline and expanded initial states differ
- a stopped or colliding trajectory is counted as recovered
- strict support is claimed without robust matched witnesses

## Evidence Gates

- freeze cells policies thresholds and disjoint seed streams before quick/full
- map physical zero throttle and brake to normalized minus one
- keep every baseline policy in the expanded policy set
- use no simultaneous pedal candidates and make no ESC claim
- require configured initial beta and yaw match plus four-wheel rear-slip truth
- count recovery only after ten stable frames with forward speed at least 4 m/s
- do not count collision spin or stopping sideways as recovery
- require matched initial hashes and exact winner replay
- require at least six robust strict full cells spanning both signs and two beta tiers
- scope support to the selected finite states and policy libraries

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use normalized zero as a physical zero pedal command
- do not call uniform braking ESC or claim individual-wheel braking
- do not remove baseline candidates from the expanded set
- do not change cells policies thresholds seeds or success rules after results
- do not count stopping sideways or low-speed settling as recovery
- do not use old audit counts as evidence
- do not mutate ActiveSafetyReflexDriver or train a policy
- do not claim all post-slip states all no-steer controls real cars promotion or self-ID

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m3271-phase5-h1-postslip-nested-recovery-certificate
- type: infrastructure
- checkpoint: None
- success_rate: 0
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: h1_quick_inconclusive
- reason: 60/60 rows action nesting and weak inclusion passed with 4/4 exact replays; reset rear slip was 0.00136 rad below the 0.15 slide-truth threshold; neither mirrored cell was strict and full was blocked

## Next Blocker

None recorded.
