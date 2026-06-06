# M2870 Engineering Controller Route A Localized Response-Prediction Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_post_localized_response_prediction_evidence_index_refresh_and_admission_synthesis`
- manifest: `experiments/manifests/m2870-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-branch-synthesis.json`
- synthesis artifact: `docs/m2870-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-branch-synthesis.md`
- parent audit: `docs/m2869-engineering-controller-route-a-response-predictive-recurrent-belief-localized-response-prediction-candidate-closed-loop-delta-panel-result-audit.md`
- parent summary: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/summary.json`
- parent surface deltas: `runs/m2868_engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel/surface_delta_rows.csv`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2871-engineering-controller-route-a-post-localized-response-prediction-evidence-index-refresh-and-admission-synthesis.json`
- next: `m2871-engineering-controller-route-a-post-localized-response-prediction-evidence-index-refresh-and-admission-synthesis`

## Evidence Summary

M2864-M2869 completed a bounded localized response-prediction branch:

```text
M2864/M2865:
  designed and audited a localized response-prediction training recipe
  with loss weights, horizon masking, rollback gates, fresh-surface guards,
  actor 72/action 3, and future-label invisibility.

M2866/M2867:
  implemented the bounded recipe and wrote a candidate checkpoint.
  status_pass: true
  gate_matrix_pass: true
  response_prediction_loss_mean: 0.24616368114948273
  actor-visible labels: false
  hidden/oracle actor input: false

M2868/M2869:
  executed and audited a paired closed-loop diagnostic delta panel.
  paired execution rows: 48
  paired delta rows: 24
  surface delta rows: 2
  surfaces: 16 M2850 explanatory rows, 8 fresh/disjoint rows
  actor contract: 72 observation / 3 action preserved
  ranking/winner/promotion/success-rate verdict: false
```

The closed-loop diagnostic result is complete but weak:

```text
baseline rows: 24, success 0, collision 1
candidate rows: 24, success 0, collision 1
termination_pair_changed_count: 0
collision_pair_changed_count: 0

fresh_disjoint:
  rows: 8
  clearance margin delta: +0.011514063063262692
  return delta: -0.15161537536197656
  speed delta: -0.01335838212578161
  high sideslip delta: -0.00474740849996998

m2850_explanatory:
  rows: 16
  clearance margin delta: +0.020778703978062613
  return delta: -0.014369599207990802
  speed delta: -0.010273789673540784
  high sideslip delta: +0.0007573888984214149
```

Route A context also matters. M2641/M2643 already produced a source-only fresh
generalization panel with 160 measured behavior rows and 12800 telemetry rows
across stable_avoidable, stable_aes, drift_required_recovery, and
unavoidable_mitigation roles. M2657/M2660 already refreshed the Route A evidence
index after target/protected reporting and kept protected mitigation failure as
blocking evidence. M2870 therefore must not route to a repeated source-only
fresh generalization panel or another same-family localized response-prediction
training loop.

## Supported Claims

M2870 supports these bounded claims:

```text
The localized response-prediction branch is artifact-complete and claim-safe.
M2866 changed the bounded response-prediction candidate checkpoint and produced
finite localized response-prediction loss evidence.
M2868 produced complete paired closed-loop diagnostic deltas on separated
M2850 explanatory and fresh/disjoint surfaces.
The candidate produced small mean clearance-margin gains but lower mean return
and speed on the audited surfaces.
Terminal success, collision, and termination outcomes did not improve.
Actor 72/action 3, future-label invisibility, and no hidden/oracle actor input
were preserved through the branch.
```

These claims are enough to route the project. They are not enough to validate,
rank, promote, publish performance, or claim a driver capability improvement.

## Falsified Or Rejected Claims

M2870 rejects these interpretations:

```text
M2866/M2868 proves repair success.
M2866/M2868 improves terminal driver capability evidence.
M2866 should be promoted over M2848.
M2868 supports checkpoint ranking, winner selection, validation, or a
success-rate verdict.
Another immediate localized response-prediction training loop is justified by
the observed deltas.
The M2850 explanatory rows can be used as ordinary validation or optimization
denominators.
The fresh/disjoint rows are large enough to support performance or promotion
claims.
```

M2870 also rejects paper-level finite-window-vs-GRU, current-sim verdict,
high-fidelity validation, full ideal driver completion, and level-3
self-identification interpretations.

## Failure Taxonomy Summary

Active failure classes:

```text
behavior_regression:
  not a strict terminal regression, but the candidate lowers mean return and
  speed while leaving terminal outcomes unchanged.

scenario_sampling_failure:
  active caution. The branch uses 16 M2850 explanatory rows and only 8
  fresh/disjoint rows, so it cannot stand in for distribution evidence.

objective_overfit:
  high for another localized response-prediction training loop because the
  branch has already converted instrumentation, localization, recipe design,
  implementation, and paired deltas without terminal improvement.

metric_artifact:
  controlled by M2868/M2869 surface separation, but a single clearance-margin
  summary would hide lower return/speed and unchanged terminal outcomes.

proof_washout:
  controlled. M2868 preserved diagnostic-only denominators and rejected
  ranking, promotion, validation, and performance claims.

contract_violation:
  not observed. Actor 72/action 3, actor-invisible labels, and no hidden/oracle
  actor inputs remain preserved.

lineage_invalid:
  not observed. M2868 corrected the M2866 actor-contract lineage guard by using
  the checkpoint manifest and guard rows rather than the summary alone.
```

## Public-Gate Overfit Risk

Public-gate overfit risk is high if the next step is another localized
response-prediction optimization pass on the same M2850 explanatory surface or
the same small fresh/disjoint complement. The branch has already used those
rows for per-step telemetry, response-prediction trace repair, localization,
recipe design, bounded implementation, and paired deltas.

Risk is lower if the next step re-indexes the whole Route A evidence state
before admitting more execution:

```text
include:
  M2541 baseline/interface evidence
  M2544 and public benchmark pack evidence
  M2639 Route A evidence index
  M2641/M2643 source-only fresh generalization panel
  M2657/M2660 target/protected report and refreshed evidence index
  M2771 negative mechanism-localized repair branch synthesis
  M2838/M2840 post Route C/HF3 stop fresh source-diverse evidence
  M2868/M2869 localized response-prediction diagnostic deltas
  M2638/M2836 Route C HF3 source blocker

exclude:
  promotion, ranking, validation, performance verdicts, paper claims,
  current-sim verdicts, high-fidelity validation claims, full-driver claims,
  and self-identification claims.
```

This follows `docs/post-m2470-route-plan.md`: Route A should move toward a
usable actuator-level active-safety controller baseline without letting
current-sim or local diagnostic artifacts become the main loop.

## Route A Progress Delta

M2870 records a process and diagnostic progress delta, not a capability delta.

Positive progress:

```text
The response-prediction branch now has closed-loop paired diagnostic evidence
instead of only implementation or loss evidence.
The branch preserved the actor/action contract and future-label boundary.
The mixed result closes a local training route that could otherwise continue
without terminal evidence.
```

Missing progress:

```text
No terminal success improvement.
No collision improvement.
No validation readiness.
No checkpoint promotion.
No driver-performance, current-sim, high-fidelity, paper, full-driver, or
self-identification evidence.
```

Therefore M2870 should not continue directly to another localized
response-prediction training recipe. It should pivot to a Route A evidence
index refresh and admission synthesis that decides the next evidence-expanding
action from the whole post-M2470 record.

## Next Branch Decision

M2870 chooses:

```text
pivot_to_route_a_post_localized_response_prediction_evidence_index_refresh_and_admission_synthesis
```

Admitted next milestone:

```text
m2871-engineering-controller-route-a-post-localized-response-prediction-evidence-index-refresh-and-admission-synthesis
```

M2871 should be a process/gate synthesis. It should refresh the Route A evidence
index after M2868/M2869 and decide exactly one next admissible action:

```text
1. freeze/package the Route A actuator-level baseline evidence if the current
   evidence is sufficient for a bounded engineering baseline artifact;
2. admit a materially fresh source-only/current-sim evidence panel if it adds a
   new evidence axis rather than repeating M2641, M2657, M2769, M2838, or M2868;
3. route to high-fidelity interface preparation only if the source/dependency
   boundary is satisfied or the action remains source-only/HF0;
4. admit bounded training only if a fresh-surface design and rollback gates
   are specified before execution;
5. stop the local Route A repair/training branch if none of the above expands
   evidence.
```

M2871 must preserve actor 72/action 3, no hidden/oracle inputs, actor-invisible
diagnostic labels, and the separation between proof, generalization, and
promotion gates. It must not run training, validation, ranking, promotion,
success-rate verdict computation, or claim driver performance, paper evidence,
current-sim verdict, high-fidelity validation, full-driver completion, or
self-identification.
