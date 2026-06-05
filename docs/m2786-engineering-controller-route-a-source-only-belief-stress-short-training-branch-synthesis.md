# M2786 Engineering Controller Route A Source-Only Belief-Stress Short-Training Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_source_only_belief_stress_fresh_holdout_delta_panel`
- manifest: `experiments/manifests/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.json`
- synthesis artifact: `docs/m2786-engineering-controller-route-a-source-only-belief-stress-short-training-branch-synthesis.md`
- parent audit: `docs/m2785-engineering-controller-route-a-source-only-belief-stress-candidate-closed-loop-delta-panel-result-audit.md`
- parent paired delta panel: `runs/m2784_engineering_controller_route_a_source_only_belief_stress_candidate_closed_loop_delta_panel/summary.json`
- parent short-training preflight: `runs/m2782_engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight.json`
- next: `m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight`

## Evidence Summary

M2778-M2785 completed a source-only Route A belief-stress short-training branch:

```text
M2778 design:
  admitted a bounded belief-stress training protocol from M2775/M2777 evidence
  preserved actor 72/action 3 and no hidden/oracle actor input
  rejected execution, training result, ranking, validation, performance, paper,
  current-sim, high-fidelity, full-driver, and self-ID claims

M2779 admission pack:
  status_pass: true
  required_artifacts_present: true
  stress curriculum rows: 24
  mitigation guard rows: 8
  actor guard rows: 7
  claim rows: 19
  gate rows: 39

M2780 audit:
  accepted M2779 completeness and claim safety
  rejected execution, training, ranking, validation, performance, paper,
  current-sim, high-fidelity, full-driver, and self-ID interpretation

M2781 design:
  admitted a bounded short-training continuation preflight
  preserved proof/generalization/promotion separation
  required mitigation rows outside ordinary denominators

M2782 short-training preflight:
  status_pass: true
  required_artifacts_present: true
  training curriculum rows: 18
  training run rows: 54
  proof holdout probe rows: 18
  proof gates: 8
  generalization gates: 6
  promotion guards: 4
  actor guards: 6
  mitigation guards: 8
  claim rows: 11
  gate rows: 18
  source checkpoint hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
  candidate checkpoint hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8

M2783 audit:
  accepted M2782 completeness and claim safety
  rejected validation, ranking, promotion, performance, paper, high-fidelity,
  full-driver, and self-ID interpretation
  routed to paired closed-loop deltas before any interpretation

M2784 paired closed-loop delta panel:
  status_pass: true
  required_artifacts_present: true
  paired execution rows: 144
  paired delta rows: 72
  proof gates: 12
  generalization gates: 6
  promotion guards: 4
  actor guards: 7
  mitigation guards: 8
  claim rows: 11
  gate rows: 22

M2785 audit:
  accepted M2784 completeness and claim safety
  rejected direct interpretation
  routed to branch synthesis
```

The branch changed the evidence state by producing a real candidate checkpoint
and paired source-vs-candidate source-only closed-loop diagnostic rows. This is
more than static bookkeeping, but the measured candidate movement is small.

M2784 paired deltas:

```text
candidate_minus_source_minimum_obstacle_clearance_m:
  min: -0.00247320301888
  median: 0.0000509575845893
  max: 0.00182393189288
  mean: 0.0000268465623094
  positive rows: 40
  negative rows: 32

candidate_minus_source_minimum_road_margin_m:
  min: 0.0014084454846
  median: 0.00242217793635
  max: 0.00331306948403
  mean: 0.00231053054465
  positive rows: 72
  negative rows: 0

candidate_minus_source_final_speed_mps:
  min: -0.00312130270881
  median: -0.00206875661844
  max: 0.00234501786528
  mean: -0.00127893918165
  positive rows: 15
  negative rows: 57

candidate_minus_source_max_abs_yaw_rate:
  min: -0.000848451111596
  median: -0.000270900676359
  max: 0.0
  mean: -0.00031237757084
  positive rows: 0
  negative rows: 66
  zero rows: 6

candidate_minus_source_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72

mean_action_delta_l1:
  mean: 0.000309530749089
  positive rows: 72
```

The positive road-margin and lower yaw-rate deltas are consistent enough to
justify a fresh holdout diagnostic. The mixed obstacle-clearance deltas and
very small action deltas block any promotion, winner, performance, or
driver-quality conclusion.

## Supported Claims

M2786 supports these bounded claims:

```text
M2778-M2785 form a complete claim-safe source-only belief-stress
short-training branch.

M2782 produced an auditable candidate checkpoint from a bounded short-training
preflight while preserving actor 72/action 3 and no hidden/oracle actor input.

M2784 produced complete paired source-vs-candidate source-only closed-loop
diagnostic artifacts over the registered belief-stress buckets.

The M2782 candidate differs from the M2655 source in closed loop, but the
difference is small and diagnostic only.

The branch is strong enough to justify a new fresh-holdout paired delta panel
using unseen seed indices, longer horizon, and the same actor/claim boundaries.
```

These claims support a next-route decision only. They do not support repair
success, driver performance, validation readiness, validation result, ranking,
winner selection, checkpoint promotion, success-rate verdict, paper evidence,
finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation,
full ideal driver completion, or level3 self-identification.

## Falsified Claims

The following claims are rejected or not admitted:

```text
M2782 proves repair success: false
M2782 candidate is promotion-ready: false
M2784 proves candidate is better than source: false
M2784 admits checkpoint ranking or winner selection: false
M2784 admits validation readiness: false
M2784 proves driver performance: false
M2784 proves paper-level evidence: false
M2784 proves finite-window-vs-GRU evidence: false
M2784 proves current-sim or high-fidelity validation: false
M2784 proves level3 self-identification: false
M2784 completes the full ideal driver gate: false
another same-surface audit or no-new-data reanalysis is the right next action: false
```

The branch also rejects a process shortcut: small source-only deltas should not
be promoted into a result by wording. They must either generalize to fresh
holdout execution rows or remain a bounded diagnostic artifact.

## Failure Taxonomy Summary

Controlled failures and risks:

```text
contract_violation:
  controlled. All branch artifacts preserve P0 observation 72, action 3, no
  hidden/oracle actor input, no actor-visible labels, and no actor input change.

lineage_invalid:
  controlled. Source and candidate checkpoint hashes are recorded, and M2779,
  M2782, M2784, and M2785 artifacts are traceable.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators,
  paired execution rows, and paired delta rows.

metric_artifact:
  controlled only by interpretation. M2784 deltas are retained as diagnostics,
  not as success-rate, ranking, or promotion fields.
```

Active failures and risks:

```text
behavior_regression:
  active. The M2784 obstacle-clearance deltas are mixed, and the branch does not
  establish behavior-quality improvement.

scenario_sampling_failure:
  active. M2784 uses the registered source-only belief-stress panel and the
  first 4 seed indices; it is not an unseen-seed holdout or validation layer.

objective_overfit:
  active if the branch keeps reusing the same 72 paired delta rows, cherry-picks
  only positive road-margin rows, or treats small source-only shifts as a
  verdict.

local_search:
  active if the next milestone is another process-only audit or same-surface
  reanalysis rather than fresh holdout rows or a route stop.
```

## Public-Gate Overfit Risk

Public-gate overfit risk is medium-high if the next action is:

```text
another M2784-like same-seed paired delta reanalysis
promotion based on road-margin-only deltas
ranking source and candidate from mixed source-only deltas
claiming belief or self-ID from stress-family labels
using mitigation reference contexts as ordinary success denominators
```

The risk is reduced by the next route only if it uses:

```text
unseen seed indices outside M2784 seed_index 0..3
all ordinary role/dynamics/stress buckets rather than cherry-picked positives
separate proof, generalization, and promotion guards
the same actor 72/action 3 no-hidden/no-oracle contract
explicit no-ranking and no-promotion claim boundaries
```

## Next Branch Decision

Decision:

```text
pivot_to_route_a_source_only_belief_stress_fresh_holdout_delta_panel
```

The branch should pivot from short-training artifact interpretation to a fresh
holdout paired closed-loop panel:

```text
next milestone:
  m2787-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-preflight

next evidence axis:
  source_only_belief_stress_fresh_holdout_delta_panel

required design constraints:
  compare M2655 source and M2782 candidate only as paired diagnostic subjects
  use unseen source-only seed indices beyond M2784 seed_index 0..3
  cover all ordinary role/dynamics/stress buckets
  use a longer horizon than M2784
  keep mitigation reference rows guarded outside ordinary denominators
  preserve actor P0 observation 72 and action 3
  expose no hidden/oracle actor features or evaluator labels to actor input
  write proof, generalization, promotion, actor, mitigation, claim, and gate rows

forbidden interpretation:
  no ranking, winner, promotion, validation, success-rate verdict, performance,
  paper, current-sim, high-fidelity, full-driver, or self-ID claim
```

This pivot is aligned with the post-M2470 Route A objective: continue building
auditable engineering-controller evidence without letting source-only diagnostics
become a performance or self-ID claim. If M2787/M2788 fresh holdout rows fail to
show a robust candidate signal, the branch should preserve the negative result
and pivot toward a broader architecture or scenario-distribution change rather
than tuning the same public surface.
