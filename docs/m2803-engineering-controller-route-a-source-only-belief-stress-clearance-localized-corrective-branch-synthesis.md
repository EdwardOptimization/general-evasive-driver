# M2803 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Corrective Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_post_clearance_corrective_readiness_index`
- manifest: `experiments/manifests/m2803-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-branch-synthesis.json`
- synthesis artifact: `docs/m2803-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-branch-synthesis.md`
- parent audit: `docs/m2802-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-result-audit.md`
- parent triad summary: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/summary.json`
- parent corrective preflight summary: `runs/m2799_engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2804-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-preflight.json`
- next: `m2804-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-preflight`

## Evidence Summary

M2796-M2802 form a complete claim-safe source-only clearance-localized
corrective branch.

The branch started from the M2796/M2797 obstacle-clearance atlas:

```text
M2796 candidate-minus-source obstacle clearance:
  positive rows: 30
  negative rows: 42
  mean: -0.0003189920460919861

M2796 candidate-minus-base obstacle clearance:
  positive rows: 29
  negative rows: 43
  mean: -0.00013214111660788612

role structure:
  drift_required_recovery: 48/48 negative
  stable_aes: 36/48 negative
  stable_avoidable: 1/48 negative
```

M2798 designed a bounded corrective update, and M2799 executed that update as
a source-only preflight from the M2791 start checkpoint:

```text
source_checkpoint_hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
M2782_base_lineage_hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
M2791_start_checkpoint_hash: 32b001944b688162ba9afb379aa6ed54f59920261d3a10ec8572d6e2da769651
M2799_candidate_checkpoint_hash: 44bedadceae2e53efaa7c37cf5be211cb8652b9088a1d7e1f237843f69ab2f20
objective rows: 18
training rows: 48
proof and retention probe rows: 48
gate rows: 31 all pass
```

M2800 accepted M2799 as complete and claim-safe preflight evidence, while
explicitly rejecting repair-success, validation, ranking, promotion,
performance, paper, current-sim, high-fidelity, full-driver, and self-ID
interpretations.

M2801 then tested the M2799 candidate on a fresh source/M2791-start/candidate
triad panel:

```text
seed indices: [12, 13, 14, 15]
previous seed indices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
horizon_steps: 160
m2793_horizon_steps: 140
triad_execution_rows: 216
candidate_minus_source_delta_rows: 72
candidate_minus_M2791_start_delta_rows: 72
proof gates: 16
generalization gates: 9
behavior-retention gates: 9
promotion guards: 4
gate rows: 38 all pass
```

M2802 audited and accepted those artifacts as complete and claim-safe. The
fresh-holdout result did not support the corrective hypothesis:

```text
candidate_minus_source_obstacle_clearance:
  positive rows: 23
  negative rows: 49
  mean: -0.00365399786071096
  median: -0.004516664759614875

candidate_minus_M2791_start_obstacle_clearance:
  positive rows: 23
  negative rows: 49
  mean: -0.001043581525003352
  median: -0.0016528113121421217

stable_avoidable_candidate_minus_source_negative_count: 4
stable_avoidable_candidate_minus_M2791_start_negative_count: 2
```

Road-margin, final-speed, yaw-rate, throttle/brake conflict, and action-delta
rows remain diagnostic side effects. They do not override the hard
obstacle-clearance and stable_avoidable retention guards.

## Supported Claims

M2803 supports these bounded claims:

```text
M2796-M2802 form a complete source-only clearance-localized corrective branch.

The branch preserved the deployable actor contract: P0 observation 72, action
3, no hidden/oracle actor input, no actor-visible atlas/role/dynamics/stress/
clearance/outcome/progress/success/route/verdict labels, and mitigation
reference rows outside ordinary denominators.

M2799 produced an auditable corrective candidate checkpoint from a bounded
preflight without promotion.

M2801 produced fresh closed-loop diagnostic evidence on seed indices 12..15
with horizon 160 and complete source/M2791-start/candidate lineage.

M2802 accepted M2801 artifact completeness and claim safety.

The branch produced a useful negative result: the clearance-localized
corrective update failed the hard obstacle-clearance interpretation test on
fresh holdout and should not be promoted or repeated as the same local repair
loop.
```

These are route-decision claims only. They are not driver-performance,
validation, promotion, paper, high-fidelity, full-driver, or self-ID claims.

## Falsified Claims

M2803 rejects or fails to support:

```text
M2799 repaired the M2796 clearance blocker: false
M2799 is better than M2655 source on fresh holdout: false
M2799 is better than M2791 start on fresh holdout: false
M2799 preserved stable_avoidable clearance retention on fresh holdout: false
M2799 is ready for checkpoint promotion: false
M2801 admits checkpoint ranking or winner selection: false
M2801 admits validation readiness or validation result: false
M2801 proves driver performance: false
M2801 proves paper evidence, finite-window-vs-GRU evidence, current-sim
  verdict, high-fidelity result, full ideal driver completion, or level3
  self-identification: false
another clearance-localized actor-head corrective update is the right next
  action: false
another same-style triad panel before route change is the right next action:
  false
```

The key scientific result is negative but useful: the local corrective update
did not generalize to the fresh clearance surface, and the branch should stop
repairing this local surface by more tiny actor-head updates.

## Failure Taxonomy Summary

Controlled:

```text
contract_violation:
  controlled. Actor observation/action contract remains 72/3 and no
  hidden/oracle actor input or actor-visible labels are introduced.

lineage_invalid:
  controlled. Source, M2782 lineage, M2791 start, and M2799 candidate hashes
  are recorded and distinct.

scenario_sampling_failure:
  controlled for M2801. Seed indices 12..15 are disjoint from prior 0..11 and
  horizon 160 is longer than M2793 horizon 140.

proof_washout:
  controlled. Mitigation reference rows stay outside ordinary denominators.

metric_artifact:
  controlled by interpretation. M2801 records road-margin, speed, yaw-rate,
  conflict, and action deltas as diagnostics, not as success-rate verdicts.
```

Active:

```text
behavior_regression:
  active. Fresh-holdout obstacle-clearance deltas are negative in 49/72 rows
  against both source and M2791 start, and stable_avoidable has negative rows.

objective_overfit:
  active if Route A hides clearance behind favorable side metrics or schedules
  another tiny corrective update over the same clearance-localized branch.

local_search:
  active if the next action is another same-axis corrective update, same-style
  triad panel, or process-only audit without a broader evidence map.

high_fidelity_dependency:
  active outside this branch. M2638 already records selected-platform HF3
  execution as paused until a valid local source root or package route is
  supplied.
```

## Public Gate Overfit Risk

Risk is high if the next action is:

```text
another M2799-like actor-head corrective update
another same-style M2801 triad panel
promotion based on road-margin, speed, yaw-rate, or action-delta positives
weakening obstacle-clearance or stable_avoidable guards
using mitigation reference rows as ordinary denominator rows
claiming Route A driver performance, paper evidence, current-sim verdict,
high-fidelity validation, full-driver completion, or self-ID from source-only
delta rows
```

Risk is lower if the next branch changes the evidence surface and integrates
the new negative clearance result with the whole Route A readiness state:
baseline checkpoint list, actor I/O contract, source-only benchmark pack,
known failure taxonomy, runtime report, scenario-role metric reports, M2638
HF3 blocker, M2749 readiness index, and the M2801/M2802 corrective-branch
negative result.

## Next Branch Decision

Decision:

```text
pivot_to_route_a_post_clearance_corrective_readiness_index
```

The next bounded route is:

```text
m2804-engineering-controller-route-a-post-clearance-corrective-readiness-index-materialization-preflight
```

M2804 should materialize a current Route A readiness/admission index from
existing artifacts only. It should integrate:

```text
M2803 synthesis and M2802 audit
M2801 fresh-holdout triad deltas and gates
M2799 corrective preflight and M2800 audit
M2749 readiness/admission index
M2748 role-panel synthesis and M2746/M2747 weak role-panel diagnostics
M2667 protected-readiness index
M2541 baseline checkpoint list and actor I/O contract
M2505 public source-only diagnostic benchmark pack
M2508 runtime/inference-cost report
M2638 HF3 source dependency blocker
docs/post-m2470-route-plan.md
```

The index should answer which Route A deliverables remain current, which
blockers are active after the failed corrective branch, and what next
non-overfit evidence route is admissible. It may admit a future execution,
new architecture/training protocol, Route B comparison, package-with-limitations,
or Route C dependency route only after preserving claim boundaries.

M2804 must not run reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, success-rate verdict computation, or performance interpretation.

Rationale:

```text
Stopping the whole project is wrong because the full ideal driver gate has not
passed.

Continuing the clearance-localized corrective branch is local search because
M2801 already produced fresh negative closed-loop evidence.

Direct validation, ranking, promotion, performance, paper, current-sim,
high-fidelity, full-driver, or self-ID interpretation is forbidden by M2802.

HF3 selected-platform execution is still blocked by M2638 until source
dependency evidence is supplied.

The highest leverage next action is to refresh Route A readiness/admission
after the corrective-branch negative result, so the project chooses the next
evidence route from the whole current artifact set instead of continuing a
narrow repair loop.
```

## Route Boundary

M2803 performs no reset, step, policy action, rollout, replay, validation,
training, PPO, source build, adapter probe, external simulation, ranking,
winner selection, promotion, success-rate computation, or performance
interpretation.

M2803 does not claim repair success, driver performance, validation readiness,
validation result, paper-level evidence, finite-window-vs-GRU, current-sim
verdict, high-fidelity validation, full ideal driver completion, or self-ID
evidence.
