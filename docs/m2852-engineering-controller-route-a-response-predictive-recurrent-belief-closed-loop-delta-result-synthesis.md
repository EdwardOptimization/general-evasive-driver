# M2852 Engineering Controller Route A Response-Predictive Recurrent-Belief Closed-Loop Delta Result Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_failure_localization_training_recipe_redesign_design`
- manifest: `experiments/manifests/m2852-engineering-controller-route-a-response-predictive-recurrent-belief-closed-loop-delta-result-synthesis.json`
- synthesis artifact: `docs/m2852-engineering-controller-route-a-response-predictive-recurrent-belief-closed-loop-delta-result-synthesis.md`
- governing route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design.json`
- next: `m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design`

## Route Plan Constraint

M2852 applies the same control rule recorded in `docs/post-m2470-route-plan.md`:
the project should stop spending milestones on artifacts that cannot change the
next admission decision. The response-predictive recurrent-belief branch has now
produced implementation, bounded continuation, paired closed-loop diagnostic
delta, and audit artifacts. The remaining question is not whether another
continuation or another same fixed delta panel can be made to run. It is whether
the branch has changed evidence enough to justify the next evidence axis.

This synthesis therefore closes the direct continuation loop and pivots to a
failure-localization and training-recipe redesign design branch. M2852 does not
run reset, step, rollout, replay, validation, training, PPO, private holdout,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or success-rate verdict computation.

## Evidence Summary

M2843 admitted a bounded Route A response-predictive recurrent-belief training
protocol. It preserved the deployed actor contract:

```text
actor observation shape: 72
action shape: 3
actor_encoder: human_view_online_gru
response prediction target indices: 0..8
response prediction horizon: 4
forbidden actor inputs: hidden dynamics, oracle labels, feasibility labels,
  source/stress/scenario-role/outcome/route/progress/verdict labels
```

The protocol required trainable recurrent and fusion groups, not another scalar
actor-head repair loop:

```text
response_encoder
online_gru_cell
response_context_fusion
actor_mean
critic
log_std
response_prediction_head
```

M2846 materialized the implementation preflight and produced a bounded 8-step
CPU PPO smoke artifact:

```text
status_pass: true
candidate checkpoint written: true
response_prediction_loss_mean: 0.3585260510444641
non-actor-head changed groups:
  response_encoder, online_gru_cell, response_context_fusion,
  response_prediction_head
actor boundary: 72/action 3, no hidden/oracle actor input
```

M2848 produced the bounded continuation preflight from the M2846 checkpoint:

```text
status_pass: true
source_load_mode: strict
total_steps: 32
rollout_steps: 16
response_prediction_loss_mean: 0.32993096113204956
changed groups:
  response_encoder, online_gru_cell, response_context_fusion,
  actor_mean, critic, log_std, response_prediction_head
actor_mean_bias_only: false
gate_matrix_pass: true
```

M2850 executed the paired diagnostic closed-loop delta panel comparing the M2846
baseline with the M2848 candidate:

```text
selected M1690 L3_online_gru pairs: 16
paired execution rows: 32
paired delta rows: 16
execution status: 32 completed
proof gates: 15/15 pass
generalization gates: 8/8 pass
promotion guards: 4/4 pass
actor guards: 17/17 pass
claim rows: 16/16 pass
gate matrix: 27/27 pass
actor boundary: 72/action 3, no hidden/oracle actor input
```

M2850 also recorded weak diagnostic outcomes:

```text
diagnostic success count: 0
diagnostic collision count: 0
termination counts:
  none/empty: 30
  speed_too_low: 2
termination pair changed: 0/16
collision pair changed: 0/16
```

The candidate-minus-baseline deltas are finite and directionally useful for
diagnosis, but not sufficient for ranking or promotion:

```text
min-clearance-margin delta positive rows: 16/16
min-clearance-margin delta mean: 0.04809967522105241
min-clearance-margin delta min: 0.009503129480249672
min-clearance-margin delta max: 0.12880645071691532
return delta positive rows: 1/16
return delta negative rows: 15/16
return delta mean: -0.7467048857331317
speed_mean delta positive rows: 1/16
speed_mean delta negative rows: 15/16
speed_mean delta mean: -0.02679994908956665
```

M2851 accepted M2850 only as complete and claim-safe paired diagnostic delta
evidence. It rejected repair success, driver performance, validation readiness,
ranking, winner selection, promotion, paper evidence, current-sim verdict,
high-fidelity validation, full-driver completion, and level3 self-identification
claims.

M2838 remains visible as weak diagnostic accounting and remains outside ordinary
success denominators:

```text
diagnostic_success_count: 1
diagnostic_collision_count: 2
diagnostic_offtrack_count: 13
ordinary_success_denominator_allowed: false
```

## Supported Claims

M2843-M2851 support these narrow claims:

```text
1. The response-predictive recurrent-belief implementation and bounded
   continuation path can produce auditable artifacts under actor 72/action 3.
2. The M2846 and M2848 checkpoints preserve the no-hidden/no-oracle actor
   boundary and do not reduce the branch to actor_mean.bias-only updates.
3. The paired closed-loop diagnostic delta panel can execute 16 fixed M1690
   L3_online_gru pairs and write complete execution, delta, guard, claim, and
   gate artifacts.
4. The M2848 candidate changed closed-loop behavior on the fixed panel in a
   finite, auditable way: clearance margin improved on all 16 paired rows.
5. The branch maintained proof, generalization, promotion, actor, and claim
   boundary separation.
```

These claims are engineering-process and diagnostic claims. They do not say the
candidate is a better driver.

## Falsified Or Unsupported Claims

The branch does not support:

```text
repair success
driver performance
validation readiness
validation result
ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation
full ideal driver completion
level3 self-identification
```

M2850 also does not support direct continuation as the next default route. The
all-positive clearance-margin deltas did not change termination outcomes, did
not produce diagnostic successes, and arrived with mostly lower return and
speed. A longer continuation or another fixed-panel delta would likely repeat
the same local-search surface unless a new failure-localization question is
defined first.

## Failure Taxonomy Summary

```text
contract_violation:
  controlled. Actor 72/action 3 and no hidden/oracle actor input were preserved.

lineage_invalid:
  controlled. M2846 and M2848 checkpoint lineage and summary artifacts are
  explicit and audited.

metric_artifact:
  controlled but still sensitive. Positive clearance deltas are preserved as
  diagnostic deltas only and are not converted into ranking or performance
  metrics.

proof_washout:
  controlled. M2850 separated 15 proof gates, 8 generalization gates, 4
  promotion guards, 17 actor guards, 16 claim rows, and 27 gate rows.

behavior_regression / weak_behavior:
  active. M2850 records zero diagnostic successes, no collision changes, no
  termination changes, mostly lower return, and mostly lower speed_mean.

objective_overfit:
  active risk. Optimizing directly against the fixed M2850 surface or the
  all-positive clearance delta could overfit a public diagnostic panel without
  solving the task.

scenario_sampling_failure:
  active caution. The 16 fixed M1690 L3_online_gru pairs are useful diagnostics,
  not validation coverage.

seed_fragility:
  active caution. The paired panel is complete but bounded; it cannot carry a
  generalization or promotion claim.
```

## Public Gate Overfit Risk

The overfit risk is high if the next task directly optimizes the M2848/M2850
surface, treats positive clearance delta as a reward target, extends the same
continuation recipe, or runs another fixed-panel delta and searches for a better
headline.

The risk is lower if the next branch changes the evidence axis from
continuation and paired-delta accounting to row-level failure localization and a
pre-registered training recipe redesign. That next branch must preserve the
M2850 paired-panel artifacts as diagnostic inputs, keep M2838 accounting outside
ordinary denominators, and avoid using public rows as the only optimization
surface.

## Next Branch Decision

M2852 selects:

```text
synthesis_decision: pivot
next_branch:
  engineering_controller_route_a_response_predictive_recurrent_belief_failure_localization_training_recipe_redesign
next_milestone:
  m2853-engineering-controller-route-a-response-predictive-recurrent-belief-failure-localization-training-recipe-redesign-design
```

The M2853 design branch should answer a different question from M2848-M2850:

```text
Why do positive clearance deltas not convert into task outcomes, and what
bounded training-recipe or diagnostic route would test that failure without
repeating direct continuation?
```

M2853 should design, but not execute, a row-level failure-localization schema and
one bounded follow-up route. Candidate localization axes include:

```text
low-speed onset and speed_too_low precursors
progress loss before the empty/none termination rows
clearance-margin timing relative to steering, throttle, and brake commands
action-response lag under the response-predictive recurrent state
response-prediction error versus closed-loop intervention timing
road-boundary/off-track margin windows
return and speed tradeoff windows where clearance improves but task progress
degrades
termination-invariance cases where both baseline and candidate fail the same
way
```

M2853 must not run the localization panel, train, validate, rank, or promote. If
the design is accepted, a later separately pre-registered milestone may produce
new diagnostics or a revised training recipe under unchanged actor boundaries.

## Claim Boundary

M2852 closes the direct response-predictive recurrent-belief continuation loop
as complete but weak diagnostic evidence. It preserves:

```text
M2850: 16 pairs, 32 execution rows, 16 paired delta rows
M2850: 0 success, 0 collision, 30 empty terminations, 2 speed_too_low
M2850: 16/16 positive clearance-margin deltas as diagnostic only
M2838: weak diagnostic accounting outside ordinary denominators
actor: 72 observation values, 3 action values, no hidden/oracle labels
claims: no validation, ranking, promotion, performance, paper, current-sim,
  high-fidelity, full-driver, or self-ID verdict
```

The allowed M2852 claim is only that a branch synthesis was completed and that
the next bounded route is M2853 failure-localization and training-recipe
redesign design.
