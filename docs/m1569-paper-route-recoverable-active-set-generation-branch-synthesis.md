# M1569 Paper-Route Recoverable Active-Set Generation Branch Synthesis

## Summary

M1569 synthesizes the recoverable active-set generation branch after M1559-M1568.

Synthesis decision:

```text
continue
```

Decision:

```text
recoverable_active_set_generation_synthesis_continue_to_one_targeted_third_source_implementation
```

The branch made real progress on source generation. It moved from sparse
terminal active-set failures to a sizeable recoverable active-set pool, then to
a source/window-balanced diagnostic set, and then to a near-miss repaired pool
with many recoverable anchors and two flip source families. It has not yet
produced a source-diverse distinct flip-anchor set that is ready for history
interventions or candidate materialization.

The next step is therefore exactly one bounded targeted implementation for the
third-source blocker designed in M1568. This is still a source-generation
milestone, not a history-necessity milestone.

## Evidence Summary

M1559 designed the recoverable active-set generation route. The core shift was
to stop replaying history interventions over rows that were already terminally
decided, and instead first mine rows where bounded local control can still move
the terminal outcome.

M1560 implemented the generator and produced:

```text
recoverable_boundary_anchor_count: 86
strong_recoverable_boundary_anchor_count: 36
predecision_recoverable_anchor_count: 80
active_source_family_count: 5
active_window_count: 5
success_flip_count: 66
collision_flip_count: 30
guardrail_violation_count: 0
passes_public_smoke_gates: false
```

M1561 audited this as a recoverable-count pass with a source-concentration
failure. The key blocker was:

```text
max_single_active_family_share: 0.45348837209302323
threshold: 0.35
```

M1562 designed a diagnostic source-balanced selector.

M1563 implemented the selector:

```text
selected_recoverable_anchor_count: 40
selected_strong_recoverable_anchor_count: 27
selected_predecision_anchor_count: 37
selected_source_family_count: 5
selected_window_count: 5
max_selected_source_family_share: 0.3
max_selected_window_share: 0.3
selected_collision_flip_anchor_count: 5
selected_success_flip_anchor_count: 5
passes_public_selector_gates: false
```

M1564 audited M1563 as a selector/source-balance pass but not a materializable
active set. The input pool itself had only five distinct collision flips and
five distinct success flips, all source-singleton in
`t5_boundary_axis_retarget`. Treating repeated local variants as independent
anchors was rejected.

M1565 designed the flip-anchor source-generation repair.

M1566 implemented and ran the bounded repair smoke:

```text
source_spec_count: 300
anchor_candidate_count: 320
replay_ok_anchor_count: 262
recoverable_boundary_anchor_count: 111
strong_recoverable_boundary_anchor_count: 59
predecision_recoverable_anchor_count: 105
active_source_family_count: 5
active_window_count: 5
max_single_active_family_share: 0.3783783783783784
distinct_collision_flip_anchor_count: 7
distinct_success_flip_anchor_count: 8
distinct_any_flip_anchor_count: 10
flip_anchor_source_family_count: 2
flip_anchor_window_count: 3
max_single_flip_source_family_share: 0.5
guardrail_violation_count: 0
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
```

This was a near-miss. It improved recoverable anchors and success flips, and it
expanded flip families from one to two, but it remained one collision flip and
one flip source family short of the public smoke gates.

M1567 audited the near-miss and identified credible third-source candidates:

```text
t5_high_speed_close_obstacle recoverable: 29
t5_high_speed_close_obstacle strong: 13
late_reveal_boundary recoverable: 18
late_reveal_boundary strong: 10
```

Both families have recoverable active-set mass but zero flip anchors. This makes
one targeted third-source implementation scientifically justified; it is not
just chasing a single row.

M1568 designed that targeted implementation, focused on:

```text
t5_high_speed_close_obstacle
late_reveal_boundary
```

with `curved_boundary_obstacle` as diagnostic bonus only. M1568 also required
the next implementation to report:

```text
third_source_flip_anchor_count
targeted_family_flip_anchor_count
```

Workflow cadence is now due, so M1569 performs branch synthesis before allowing
that implementation.

## Supported Claims

The branch supports these claims:

```text
multi-step local holds can expose many recoverable terminal-boundary anchors;
recoverable active-set anchors can be generated across five source families and five temporal windows;
a source/window-balanced diagnostic subset can be selected without rerunning simulation;
variant counts are not a substitute for distinct flip anchors;
the repaired generator improves distinct success flips and adds a second flip source family;
high-speed and late-reveal families are credible third-source targets because they have strong recoverable mass but zero flips;
one bounded targeted third-source implementation is justified before closing or pivoting the branch.
```

## Unsupported Claims

The branch does not support:

```text
history necessity;
wrong-history success-drop evidence;
level3 anticipatory self-identification;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level result claims;
actor input contract changes.
```

M1559-M1568 are source-generation and process evidence only. They do not run
wrong-history, delayed-history, reset-hidden, zero-history, or donor-history
interventions.

## Falsified Claims

The branch falsifies or narrows these working hypotheses:

```text
1. Pair-expanded terminal rows were history-null only because the active-set miner lacked local controls.
2. Source balancing over the M1560 pool alone is enough to create materializable source-diverse flip anchors.
3. Local-hold variant counts can substitute for distinct anchor IDs.
4. Broad repaired source generation already produces a third flip source family.
```

The fourth claim is only narrowly rejected. M1566 moved from one to two flip
source families and found strong recoverable mass in high-speed and late-reveal
families, so the branch still admits one targeted test.

## Failure Taxonomy Summary

Primary failure taxonomy:

```text
scenario_sampling_failure
```

The current blocker is not training instability, PPO washout, contract
violation, or metric artifact. The source-generation distribution has not yet
produced enough source-diverse distinct flip anchors for a history-intervention
corpus.

The branch also carries a public-gate governance risk: repeated repairs have
been evaluated against public source-generation thresholds. That risk is
controlled by allowing only one targeted implementation and requiring an audit
after it, regardless of pass or fail.

## Public-Gate Overfit Risk

Public-gate overfit risk is moderate to high.

The branch has repeatedly optimized around public active-set counts:

```text
recoverable anchor count;
strong recoverable anchor count;
source-family share;
distinct collision/success flip anchors;
flip source-family count;
flip window count.
```

The risk is bounded because the next route is not another broad generator. It
targets two families that M1566 independently exposed as strong recoverable
but flip-null:

```text
t5_high_speed_close_obstacle
late_reveal_boundary
```

The next implementation must not pass by only improving the already-flipping
families:

```text
t5_boundary_axis_retarget
t5_near_boundary_warmup
```

It must separately report third-source and targeted-family flip counts.

## Next Branch Decision

Continue the same branch for exactly one bounded targeted implementation:

```text
m1570-paper-route-targeted-third-source-flip-anchor-implementation
```

M1570 should implement the M1568 design and run one bounded public smoke over
the targeted third-source families. It must not run history interventions,
materialize candidates, export a training corpus, train, use PPO, promote a
checkpoint, use private holdout, alter actor inputs, or claim self-ID.

Minimum public gates for M1570:

```text
source_spec_count >= 300
anchor_candidate_count >= 320
replay_ok_anchor_count >= 160
recoverable_boundary_anchor_count >= 48
strong_recoverable_boundary_anchor_count >= 16
active_source_family_count >= 5
active_window_count >= 5
distinct_collision_flip_anchor_count >= 8
distinct_success_flip_anchor_count >= 8
flip_anchor_source_family_count >= 3
third_source_flip_anchor_count >= 1
targeted_family_flip_anchor_count >= 1
flip_anchor_window_count >= 3
max_single_flip_source_family_share <= 0.60
guardrail_violation_count == 0
history_interventions_executed == false
candidate_materialized == false
training_corpus_exported == false
```

Hard stop:

```text
If M1570 has flip_anchor_source_family_count < 3, the following milestone must
be branch synthesis or pivot, not another generator implementation.
```

If M1570 passes, the following milestone is still a result audit before any
history-intervention design.

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1570-paper-route-targeted-third-source-flip-anchor-implementation
```
