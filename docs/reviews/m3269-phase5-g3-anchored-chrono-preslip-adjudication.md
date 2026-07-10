# m3269-phase5-g3-anchored-chrono-preslip-adjudication Research Review

## Summary

- Generated at UTC: 20260710T093120Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: g3_full_inconclusive
- Decision reason: quick passed; full finite comparisons favored pooled grip over required-slide by 6.8 m at mu 0.60 and 3.9 m at mu 0.90 with all best free trajectories grip-like and no counterexample; mu 0.35 slide 0/2 and mu 0.90 slide 1/2 made completeness fail; optimizer route closed

## Hypothesis

A final fresh-seed Chrono Phase-5 G3 panel can use M3267's exactly replayed required-slide trajectory as a preregistered feasibility anchor, without extra authority or changed criteria, to obtain stable dedicated and pooled grip/slide/free minimum-clearable-distance boundaries across three frozen friction cells and adjudicate the 0.25 m bounded no-drift advantage rule before any universal theorem, real-vehicle, paper-readiness, promotion, or self-ID claim.

## Lineage

- parent_checkpoint: docs/preslip-reachable-set-dual-proof-theory-2026-07.md, docs/m3267-phase5-g1-preslip-reachable-set-adjudication.md, docs/m3268-phase5-g2-chrono-preslip-boundary-adjudication.md, docs/current-status.md
- parent_dataset: experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick.json, experiments/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication_quick.json
- parent_config: scripts/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication.py, scripts/feasibility_audit/phase5_g2_chrono_preslip_boundary_adjudication.py, scripts/feasibility_audit/phase5_g3_anchored_chrono_preslip_adjudication.py
- parent_objective: adjudicate the finite detailed-model bridge for the bounded pre-slip theorem, remove known-feasible narrow-set recall as an optimizer confound
- derived_from: M3267 exact-replay required-slide D-star 21.7 m at mu 0.48 and 16 m/s, M3268 fresh seed missed that known nonempty same-cell slide set, the anchor is frozen by source seed, array shape, float64 SHA256, insertion index, and search distance
- blocked_by: post-slip recovery and paper claim remain separate even if G3 passes
- supersedes: unanchored small-budget CEM as the sole narrow required-slide feasibility source
- invalidates: additional optimizer-only repairs after G3, omitting M3267 planar incompleteness, giving the slide arm extra actuators, universalizing selected Chrono cells

## Success Criteria

- preregistration freezes anchor hash before quick/full
- quick passes all gates before full
- managed resumable full completes three cells and two seeds per arm
- all dedicated, pooled, free, strict-seed, frame, tire, and replay gates pass
- decision follows the frozen rule and raw evidence is persisted
- scope and prior negative evidence remain explicit

## Failure Criteria

- full runs before passing quick
- anchor or criteria change after inspection
- any failed arm/seed is hidden
- invalid slide is counted
- another optimizer repair is proposed after failure

## Evidence Gates

- freeze source anchor hash and insertion semantics before quick/full
- run canonical quick before managed checkpointed full
- use fresh disjoint optimizer seeds with identical per-arm budgets
- retain true OBB contact and frozen grip/controlled-slide/free predicates
- require every dedicated arm/seed and pooled arm finite
- require free consistency and worst-grip-seed versus best-slide-seed <=0.25 m
- require local frame, axle tire truth, and exact replay
- report counterexamples and M3267 planar incompleteness at full fidelity
- stop the detailed-model optimizer route on any failed G3 gate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not alter anchor, cells, budgets, modes, geometry, pooling, or tolerance after results
- do not count post-contact, unstable, stopped, off-road, or colliding slide
- do not hide dedicated rows behind pooled minima
- do not run another local search repair if G3 fails
- do not mutate ActiveSafetyReflexDriver or train a policy
- do not claim planar, split-mu, moving-obstacle, cross-vehicle, real-car, paper-readiness, promotion, or self-ID coverage

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m3269-phase5-g3-anchored-chrono-preslip-adjudication
- type: infrastructure
- checkpoint: None
- success_rate: 0
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: g3_full_inconclusive
- reason: quick passed; full finite comparisons favored pooled grip over required-slide by 6.8 m at mu 0.60 and 3.9 m at mu 0.90 with all best free trajectories grip-like and no counterexample; mu 0.35 slide 0/2 and mu 0.90 slide 1/2 made completeness fail; optimizer route closed

## Next Blocker

None recorded.
