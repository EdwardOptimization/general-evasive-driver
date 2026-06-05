# M2771 Engineering Controller Route A Action-Response Mechanism-Localized Bounded Repair Result Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_source_only_action_response_belief_intervention_design`
- manifest: `experiments/manifests/m2771-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-result-synthesis.json`
- synthesis artifact: `docs/m2771-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-result-synthesis.md`
- parent audit: `docs/m2770-engineering-controller-route-a-action-response-mechanism-localized-bounded-repair-execution-result-audit.md`
- parent summary: `runs/m2769_engineering_controller_route_a_action_response_mechanism_localized_bounded_repair_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- HF3 blocker: `docs/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.md`
- follow-up manifest: `experiments/manifests/m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design.json`
- next: `m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design`

## Evidence Summary

M2766-M2770 completed a full mechanism-localized repair branch:

```text
M2766 no-rollout mechanism-localization panel:
  telemetry join rows: 12
  mechanism-localization rows: 12
  repair-admission rows: 12
  bounded repair-design candidates: 8
  context-only rows: 4
  guardrails: 31
  primary mechanisms: 7 track-containment, 1 obstacle-timing, 4 diagnostic-success

M2768 design:
  admitted exactly 8 bounded repair rows
  preserved 4 context-only rows
  admitted only bounded actor-head bias candidates
  rejected ranking, winner selection, promotion, validation, and performance claims

M2769 bounded execution:
  repair checkpoint rows: 3
  candidate-resolution rows: 24
  baseline join rows: 8
  repair execution rows: 24
  repair execution failure rows: 0
  actor-contract guard rows: 10
  claim-boundary rows: 11
  gate rows: 20
  status_pass: true

M2770 audit:
  accepted artifact completeness and claim safety
  rejected repair-success interpretation
  routed to branch synthesis
```

The result is complete, but negative for the tested repair family:

```text
diagnostic success: 0/24
diagnostic collision: 3/24
off_track: 17/24
speed_too_low: 4/24
obstacle_collision: 3/24
success_rate_diagnostic: 0.0
collision_rate_diagnostic: 0.125
clearance_margin_mean_diagnostic: 8.995123866381123
```

The branch changed process and diagnostic evidence, but not driver capability.
It showed that a bounded actor-head brake/throttle bias sweep is not enough to
recover the admitted mechanism-localized current-sim repair surface.

The source-only and HF route context matters:

```text
M2488/M2492:
  source-only HF0 closed-loop actor path is live
  same-contract 72/3 actor can execute through source-only fixtures

M2641/M2643:
  source-only fresh generalization panel produced 160 measured behavior rows
  road-departure and drift-recovery gaps remain visible

M2655:
  target preservation gates passed
  protected mitigation component gates failed
  repaired checkpoint was not promoted

M2638 current blocker:
  /home/quyaonan/workspace/chrono remains unavailable
  pychrono and projectchrono remain unavailable
  external selected-platform HF3 execution remains paused
```

Therefore this synthesis should not route to another current-sim actor-head
bias repair or direct HF3 source build/probe. The next useful evidence axis is
to test whether the driver is failing because recurrent action-response belief
is not being used robustly across source-only role/dynamics variation.

## Supported Claims

M2771 supports these bounded claims:

```text
M2766-M2770 form a complete claim-safe mechanism-localized repair branch.
M2769 executed or accounted for all 24 registered repair candidate pairs with
0 execution failure rows.
M2769 preserved the 8 repair rows, 4 context-only rows, and 31 guardrails.
M2769 preserved actor 72/action 3 with no hidden/oracle actor input, no actor
input contract change, no active config overwrite, and no environment
relaxation.
The tested actor-head bias repair family produced negative diagnostic evidence:
0/24 success and 3/24 collision.
The next branch must change the evidence axis rather than repeating the same
8-row current-sim repair surface.
```

These claims are enough to route, not enough to validate. They do not support
repair success, controller ranking, promotion, driver performance, high-fidelity
validation, paper evidence, full-driver completion, or self-identification.

## Falsified Claims

The following claims are falsified or not admitted:

```text
M2769 proves repair success: false
M2769 improves driver capability evidence: false
M2769 admits a winner among the three repair candidates: false
M2769 admits checkpoint promotion: false
M2769 supports a success-rate verdict: false
M2769 supports current-sim validation: false
M2769 supports driver-performance evidence: false
M2769 supports high-fidelity validation: false
M2769 supports paper-level finite-window-vs-GRU or self-ID evidence: false
M2769 supports full ideal driver completion: false
```

Another immediate mechanism-localized actor-head bias sweep is also rejected.
The branch already tested three bounded bias candidates across the complete
admitted surface and got 0/24 diagnostic success. More bias sweeps on the same
rows would be local search unless a synthesis first identifies a new evidence
axis.

Direct HF3 execution is also not admitted. The source dependency required by
M2638 is still absent in the current local environment.

## Failure Taxonomy Summary

Active failures and risks:

```text
behavior_regression:
  active. M2769 has 3 obstacle-collision rows and 17 off_track rows, so the
  bounded repair did not recover closed-loop behavior.

scenario_sampling_failure:
  active caution. The repair surface is only 8 admitted current-sim rows and
  cannot stand in for distribution-level validation.

objective_overfit:
  high if the next step is another actor-head bias sweep or same-surface
  current-sim repair.

metric_artifact:
  controlled. M2769 keeps diagnostic metrics separate from verdict metrics,
  but a single success-rate summary would hide the difference between
  offtrack, collision, and speed_too_low outcomes.

proof_washout:
  controlled. The 4 context-only rows and 31 guardrails remain outside
  execution and ordinary denominators.

contract_violation:
  not observed. Actor observation 72/action 3 and no hidden/oracle labels are
  preserved.

lineage_invalid:
  not observed. M2766-M2770 artifacts, docs, manifests, and reviews are
  traceable.
```

The failure pattern points away from scalar actor-head bias repair and toward a
belief/action-response or training-recipe question: can the actor use its
recurrent state and command-response history to adapt across dynamics and role
variation, or is the current policy mostly a fragile current-response
controller?

## Public-Gate Overfit Risk

Public-gate overfit risk is high for:

```text
another M2769-like repair sweep
ranking the three M2769 repair candidates
counting the 4 context-only rows as repair wins
hiding the 31 guardrails
weakening collision/offtrack interpretation into one aggregate success metric
claiming validation, performance, paper, current-sim, high-fidelity, or self-ID
evidence from the complete but negative M2769 artifacts
```

Risk is lower if the next branch changes surface and question:

```text
surface:
  repo-local source-only HF0/four-wheel roles and dynamics axes, not only the
  same 8 current-sim repair rows

question:
  recurrent action-response belief/intervention, not scalar actor-head bias

claim:
  diagnostic mechanism evidence only, no ranking, validation, promotion, or
  driver-performance claim
```

This keeps current-sim as a diagnostic/mining layer, respects the M2638 HF3
source blocker, and moves the project back toward the long-term requirement:
a closed-loop driver that adapts from deployable observations, history,
actuator state, and recurrent state.

## Next Branch Decision

M2771 chooses:

```text
pivot_to_route_a_source_only_action_response_belief_intervention_design
```

Admitted next milestone:

```text
m2772-engineering-controller-route-a-source-only-action-response-belief-intervention-design
```

M2772 should be design-only. It should define a bounded source-only HF0
action-response belief intervention panel that can later test, under the same
72/3 actor contract, whether recurrent state and command-response history are
actually carrying useful control information across source-only role and
dynamics variation.

The design should use existing repo-local evidence and surfaces:

```text
M2488/M2492 source-only closed-loop path
M2641/M2643 source-only fresh generalization panel
M2655 mitigation-preserving checkpoint and negative protected gates
M2766-M2770 mechanism-localized current-sim negative repair branch
M2638 HF3 source dependency blocker
```

Required design constraints for M2772:

```text
use repo-local source-only HF0/FourWheel surfaces only
preserve P0 observation shape 72 and action shape 3
use deployable actor observations only
keep role, dynamics, intervention, outcome, success, progress, and verdict
labels actor-invisible
separate normal recurrent evaluation from evaluator-only reset/zero-history or
wrong-history interventions
require fresh source-only rows or axes beyond the M2769 8-row repair surface
reject candidate ranking, winner selection, promotion, success-rate verdict,
driver performance, current-sim verdict, high-fidelity validation, paper, and
self-ID claims
```

Rejected alternatives:

```text
continue same current-sim repair:
  Rejected. M2769 is complete and negative.

direct Route C HF3 execution:
  Rejected. M2638 source dependency remains unavailable.

package-with-limitations refresh:
  Useful later, but it would be process evidence and would not test the
  recurrent belief/action-response hypothesis.

Route B paper verdict:
  Premature. The next branch may create mechanism evidence, but M2771 itself
  does not run a fair controller-family matrix or claim self-ID.
```

## Claim Boundary

Allowed M2771 claim:

```text
M2766-M2770 completed a claim-safe but negative mechanism-localized repair
branch, and the active route should pivot to a new source-only action-response
belief intervention design rather than continue same-surface actor-head repair.
```

Rejected claims remain rejected:

```text
repair_success=false
driver_performance=false
validation_readiness=false
validation_result=false
ranking_or_winner_selection=false
checkpoint_promotion=false
success_rate_verdict=false
paper_evidence=false
finite_window_vs_gru_conclusion=false
current_sim_verdict=false
high_fidelity_validation=false
full_ideal_driver_completion=false
level3_self_identification=false
```
