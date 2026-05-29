# M1548 Paper-Route Fresh Ambiguity Source-Mining Branch Synthesis

## Summary

M1548 synthesizes the M1538-M1547 continuation after the M1537 branch
synthesis. The decision is:

```text
fresh_ambiguity_source_mining_synthesis_promote_to_calibrated_pair_expansion_branch
```

Synthesis decision:

```text
promote_to_next_branch
```

The current branch produced useful evidence, but it has reached the point where
more small terminal-boundary repairs inside the same loop would mainly optimize
the public gates. M1538 remains a source-expanded non-terminal positive result.
M1544 repaired the earlier terminal source-window miss by producing calibrated
near-boundary terminal rows. M1547 then showed that the remaining blocker is
not replay determinism or actor input contract, but calibrated matched-pair
coverage: only two accepted pairs on one source-family edge, with null history
and control terminal-margin effects.

The next route is a new branch:

```text
paper_route_calibrated_pair_expansion
```

No candidate materialization, corpus export, training, PPO, checkpoint
promotion, private holdout, actor-input change, or level3 self-identification
claim is admitted.

## Evidence Summary

### M1538 Source-Expanded Intervention Repeat

M1538 was the strongest positive result in this branch segment:

```text
source rows: 28
trace rows: 2497
pair candidates: 18
accepted pairs: 13
accepted source-family edges: 11
T5 / terminal-boundary accepted pairs: 5
intervention rows: 260
anchor replay failures: 0
wrong-history max margin gap: 0.1224
donor-response/action-plus-hidden max margin gap: 0.1260
max reset/zero-control gap: 0.0933
```

This supports source-expanded public history-intervention sensitivity on
non-terminal rows. It does not support terminal-boundary self-identification,
because T5/terminal-boundary history-positive target sides remained zero.

### M1539-M1542 Terminal-Boundary Repair

M1539 correctly blocked materialization and routed to terminal-boundary repair.
M1540 designed the repair. M1541 implemented the bounded repair smoke:

```text
source specs: 35
terminal target traces: 20
accepted terminal pairs: 11
accepted source-family edges: 8
intervention rows: 880
terminal target near-boundary count: 0
terminal wrong-history positive target sides: 0
terminal donor-plus-hidden positive target sides: 0
max history margin gap: 0.0040
max reset/zero-control gap: 0.1485
control/history ratio: 36.89
```

M1542 classified this as a source-window miss plus control-dominated terminal
history null. The repair plumbing was useful, but the target traces did not
enter the intended near-boundary active set.

### M1543-M1545 Task Sampling Calibration

M1543 designed task sampling around actual fixed-policy margins. M1544
implemented it and repaired the source-window issue:

```text
terminal base source rows: 10
calibration specs: 100
target traces: 57
accepted calibrated rows: 8
accepted terminal families: 4
decision-window hits: 4
post-decision-window hits: 5
terminal-window hits: 5
max single terminal-family share: 0.25
guardrail violations: 0
```

M1545 audited this as enough for design-only calibrated interventions, with
caveats: the accepted set is small, lacks `late_reveal_boundary`, has no
preferred decision-window hits, and includes collision/post-decision rows.

### M1546-M1547 Calibrated Intervention

M1546 designed the correct next test: rerun calibrated sources into measured
response/context snapshots, build matched current-state/scene pairs, then run
history/control interventions.

M1547 implemented that smoke:

```text
accepted calibrated source count: 8
measured trace count: 8
measured snapshot count: 10
measured trace family count: 4
accepted pair count: 2
accepted source-family edge count: 1
max single pair source-edge share: 1.0
intervention rows: 40
anchor replay failures: 0
terminal wrong-history positive target sides: 0
terminal donor-plus-hidden positive target sides: 0
terminal donor stream positive target sides: 0
terminal wrong-or-donor success drops: 0
terminal max history margin gap: 0.0
terminal max control margin gap: 0.0
guardrail violations: 0
```

M1547 is therefore clean plumbing, not positive history evidence. The accepted
pair set is too narrow, and the null result only applies to that narrow subset.

## Supported Claims

Supported:

```text
M1538 provides source-expanded public non-terminal wrong-history and
donor-plus-hidden terminal-margin sensitivity;
fixed-policy terminal-boundary task calibration can produce actual near-boundary
terminal rows;
calibrated measured trace reconstruction and intervention replay are feasible;
the actor contract remains P0 human-view/no-privileged throughout this branch;
the immediate terminal-boundary blocker is calibrated matched-pair coverage.
```

## Unsupported Or Falsified Claims

Unsupported:

```text
terminal-boundary history-positive evidence;
T5 terminal wrong-history success-drop evidence;
calibrated pair construction is already source-diverse enough;
candidate materialization;
training corpus export;
paper-level evidence;
level3 anticipatory self-identification;
policy superiority.
```

Falsified for this branch:

```text
M1541-style terminal repair can find near-boundary active-set rows without task
sampling calibration;
M1544 accepted calibrated rows are sufficient by themselves for source-diverse
matched-pair intervention evidence;
the M1547 two-pair calibrated subset can justify terminal-boundary
materialization or self-ID claims.
```

## Failure Taxonomy Summary

Failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure`:

```text
M1541 missed the intended terminal active set; M1547 accepted only two measured
pairs on one source-family edge, below the pre-registered pair and diversity
thresholds.
```

`metric_artifact`:

```text
M1538 non-terminal margin sensitivity is real enough to preserve as public
diagnostic evidence, but it cannot be used as terminal-boundary self-ID proof.
M1547's null terminal-history result is also not global; it is measured on a
pair-narrow subset.
```

No contract violation, private holdout contamination, PPO washout, checkpoint
promotion misuse, or training instability occurred in this branch segment.

## Public-Gate Overfit Risk

Risk:

```text
high
```

Reasons:

```text
all evidence is public development evidence;
the branch has repeatedly adapted around public terminal-boundary failures;
M1547 accepted only two pairs on one source-family edge;
M1538 positives remain non-terminal and control-sensitive;
the terminal-boundary route has not yet produced history-positive target sides.
```

This risk blocks materialization and paper-level claims. It also blocks another
small repair inside the same branch. The next experiment must start a new
branch with pair diversity as a first-class objective.

## Next Branch Decision

Promote to a new no-training branch:

```text
paper_route_calibrated_pair_expansion
```

Next manifest:

```text
m1549-paper-route-calibrated-pair-expansion-design
```

The M1549 design must address M1547 directly:

```text
pairability before interventions;
accepted pair count and source-family edge thresholds;
max single-edge share cap;
separate decision/post-decision/terminal-window buckets;
same history/control intervention channels;
no candidate materialization, training, PPO, private holdout, or actor-input
change.
```

Stop conditions for the new branch:

```text
accepted pair count remains below threshold;
accepted source-family edge count remains below threshold;
terminal-boundary history effects remain null after pair expansion;
reset/zero-current controls dominate history interventions;
any guardrail violation.
```

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```
