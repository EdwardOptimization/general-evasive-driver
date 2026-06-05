# M2795 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Candidate Triad Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_source_only_belief_stress_obstacle_clearance_regression_atlas`
- manifest: `experiments/manifests/m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-triad-branch-synthesis.json`
- synthesis doc: `docs/m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-triad-branch-synthesis.md`
- parent audit: `docs/m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit.md`
- parent triad summary: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/summary.json`
- parent training preflight summary: `runs/m2791_engineering_controller_route_a_source_only_belief_stress_guardrailed_multi_objective_training_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-preflight.json`
- next: `m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-preflight`

## Evidence Summary

M2790-M2794 form a complete claim-safe source-only guardrailed belief-stress
candidate branch. M2790 designed the hard obstacle-clearance guard. M2791 wrote
a bounded guardrailed candidate checkpoint, not a promoted checkpoint:

```text
source_checkpoint_hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
base_candidate_checkpoint_hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
M2791_candidate_checkpoint_hash: 32b001944b688162ba9afb379aa6ed54f59920261d3a10ec8572d6e2da769651
M2791_objective_rows: 18
M2791_training_rows: 54
M2791_proof_rows: 36
M2791_gate_rows: 30 all pass
```

M2793 then tested the M2791 candidate in a fresh-holdout triad panel over seed
indices 8, 9, 10, and 11, disjoint from prior seed_index 0..7, with horizon
140 greater than M2787 horizon 120:

```text
triad_execution_rows: 216
candidate_minus_source_delta_rows: 72
candidate_minus_base_delta_rows: 72
proof_gates: 16
generalization_gates: 9
behavior_retention_gates: 6
promotion_guards: 4
gate_rows: 35 all pass
```

The diagnostic deltas show that road-margin and final-speed row accounting
move in a favorable direction, but the hard clearance guard remains mixed and
skew negative:

```text
candidate_minus_source_obstacle_clearance:
  positive rows: 30
  negative rows: 42
  mean: -0.0003189920460919861
  median: -0.0026030437199309198

candidate_minus_base_obstacle_clearance:
  positive rows: 29
  negative rows: 43
  mean: -0.00013214111660788612
  median: -0.00039442807985579087

candidate_minus_source_road_margin:
  positive rows: 72/72

candidate_minus_base_road_margin:
  positive rows: 71/72

candidate_minus_source_final_speed:
  positive rows: 72/72

candidate_minus_base_final_speed:
  positive rows: 70/72
```

Actor and claim boundaries stay intact throughout the branch: P0 observation
72/action 3, no hidden/oracle actor input, actor-invisible labels, mitigation
rows outside ordinary denominators, no validation, no ranking, no winner
selection, no promotion, no success-rate verdict, no performance claim, no
paper result, no current-sim or high-fidelity verdict, no full-driver claim, and
no self-ID claim.

## Supported Claims

The branch supports these limited claims:

```text
1. M2791 produced an auditable source-only guardrailed candidate checkpoint.
2. M2793 produced complete fresh-holdout source/base/candidate closed-loop
   diagnostic rows over a new seed surface.
3. The M2791 candidate creates measurable source-only behavior movement,
   especially in road-margin and final-speed row accounting.
4. The actor contract and claim boundary can be preserved through a bounded
   training/update preflight and fresh-holdout triad panel.
5. The branch identified obstacle-clearance retention as the dominant active
   blocker before any promotion or performance interpretation.
```

## Falsified Or Rejected Claims

The branch rejects or fails to support:

```text
candidate-better-than-source verdict: rejected
candidate-better-than-base verdict: rejected
validation readiness/result: rejected
checkpoint ranking: rejected
winner selection: rejected
checkpoint promotion: rejected
success-rate verdict: rejected
repair success: rejected
driver performance: rejected
paper-level result: rejected
current-sim verdict: rejected
high-fidelity validation: rejected
full ideal driver completion: rejected
level3 self-identification: rejected
```

The key falsification is not that every metric failed. It is narrower and more
important: road-margin and speed positives do not overcome the hard obstacle-
clearance guard. Both source and base comparisons retain more negative than
positive clearance rows on fresh holdout.

## Failure Taxonomy Summary

```text
contract_violation:
  controlled. Observation/action contract and hidden/oracle exclusion remain
  intact.

lineage_invalid:
  controlled. Source, base-candidate, and M2791 candidate hashes are present
  and distinct.

scenario_sampling_failure:
  controlled for this branch. M2793 uses seed_index 8..11 disjoint from prior
  0..7 and covers all ordinary role, dynamics, and stress buckets.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators.

objective_overfit:
  active risk. The branch can be overread if road-margin or final-speed gains
  are allowed to hide clearance regressions.

behavior_regression:
  active blocker. Obstacle-clearance deltas are mixed with 42 negative
  candidate-minus-source rows and 43 negative candidate-minus-base rows.

metric_artifact:
  active risk. The M2791 actor-head update is tiny and the evidence remains
  source-only, so small row deltas may be metric artifacts rather than robust
  driver behavior.
```

## Public Gate Overfit Risk

Public-gate overfit risk is medium-high if the branch continues by repeating
the same guardrailed candidate update or adding more same-axis triad panels.
The existing rows already show the pattern clearly: road-margin and speed can
look better while clearance remains mixed. Another same-style source-only panel
would likely increase confidence in the diagnostic pattern but would not change
the blocked interpretation.

Risk is lower if the next branch changes the evidence axis to a failure atlas:
identify which role, dynamics, stress, seed, and delta families carry the
clearance negatives, classify whether the regression is systematic or localized,
and use that attribution to design the next training or architecture change.

## Next Branch Decision

Decision: pivot to a source-only obstacle-clearance regression atlas.

The next milestone is M2796. It should consume M2793/M2794 artifacts and
materialize a stratified failure atlas for the clearance-negative rows, including
role family, dynamics axis, stress family, seed index, source-vs-base contrast,
road-margin/speed/yaw-rate side effects, and claim boundaries. It should not run
new policy actions, rank checkpoints, promote, validate, or claim performance.

This is a pivot rather than a continuation because the next work changes the
evidence axis from "does this candidate look better on another holdout panel?"
to "where and why does the hard clearance guard fail?" That is the higher
leverage input for a future controller/training recipe than another same-axis
candidate panel.

M2796 must keep the same actor and claim boundaries:

```text
actor P0 observation 72/action 3
no hidden/oracle actor input
no actor-visible role/dynamics/stress/outcome/route/verdict labels
mitigation rows outside ordinary denominators
no validation, ranking, winner, promotion, success-rate, performance, paper,
current-sim, high-fidelity, full-driver, or self-ID claim
```
