# M836 V4 Full Wrong-History Response Intervention Audit

## Purpose

M836 audits the M835 full wrong-history response/action intervention result
before any new implementation.

The audit question is:

```text
Does M835 provide response-history evidence, or should the branch pivot away
from more no-training counterfactual intervention mining?
```

M836 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m835_v4_full_wrong_history_response_intervention/summary.json
runs/m835_v4_full_wrong_history_response_intervention/variant_summary.csv
runs/m835_v4_full_wrong_history_response_intervention/response_intervention_replay_rows.csv
runs/m835_v4_full_wrong_history_response_intervention/diversity_summary.json
docs/m835-v4-full-wrong-history-response-intervention-implementation.md
```

M835 result class:

```text
v4_full_wrong_history_response_intervention_all_weak
```

## Artifact Consistency

M835 produced a complete no-training diagnostic:

```text
raw_pair_rows: 60
selected_pair_rows: 60
reconstructed_snapshot_rows: 16
response_intervention_replay_rows: 540
rejected_rows: 0
```

Each variant has `60` replay rows:

```text
normal
wrong_hidden_only
wrong_ego_response_obs
wrong_action_history_obs
wrong_response_action_obs
wrong_ego_response_hidden
wrong_action_history_hidden
wrong_response_action_hidden
zero_command_obs
```

This is not an artifact-completeness failure.

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

The intervention swapped only deployable observation fields. It did not add
hidden parameters, oracle labels, or fault labels to actor input.

## Variant Audit

M835 shows action drift without outcome evidence.

Best action drifts:

```text
wrong_response_action_hidden: 0.019600431767721204
wrong_action_history_hidden:  0.017168803000693903
wrong_response_action_obs:    0.014695116575514424
zero_command_obs:             0.03573703003115858
```

The action threshold is:

```text
action_l2_threshold: 0.014
```

So some response/action variants do move the action enough to be visible.

But margin gaps stay far below the proof threshold:

```text
wrong_response_action_hidden max_gap: 0.00030215729621496656
wrong_response_action_obs max_gap:    0.0002744146905726552
wrong_action_history_hidden max_gap:  0.0002169713213744373
wrong_action_history_obs max_gap:     0.0001976526344089624
zero_command_obs max_gap:             0.004670113250027308
```

The primary margin threshold is:

```text
primary_margin_gap_threshold: 0.01
```

No variant creates a success drop or accepted row:

```text
accepted_primary_response_history_rows: 0
accepted_component_attribution_rows: 0
accepted_mitigation_rows: 0
zero_command_component_like_rows: 0
```

## Interpretation

M835 rules out a narrower explanation of M832:

```text
M832 hidden-only injection was not weak only because hidden state was the wrong
implementation detail.
```

Even direct current response/action observation swaps are outcome-weak on the
M832 near-boundary pairs.

This does not prove response-history self-ID is impossible. It does show that
the current M568/M761 behavior does not exhibit that mechanism under the
counterfactual probes built so far.

## Failure Taxonomy

### metric_artifact

Primary label. Action drift exists, but action drift alone is not self-ID proof
because terminal margin and success outcomes do not move enough.

### scenario_sampling_failure

Secondary label. The input remains the M832 `60` pair corpus, below the
pre-registered source-diverse pair target. But this is not the whole story:
even the strongest variants are two orders of magnitude below the margin gate.

### not contract_violation

No forbidden inputs or parameter updates occurred.

## Supported Claims

M835 supports:

- response/action observation interventions are implemented;
- current response/action fields influence first actions more than hidden-only;
- those action changes are not outcome-effective on the current pair set;
- more no-training wrong-history variants are unlikely to be the immediate
  highest-leverage next step.

## Unsupported Claims

M835 does not support:

- primary response-history self-ID proof;
- component attribution proof;
- mitigation proof;
- zero-command dominated proof;
- PPO admission;
- checkpoint promotion.

## Next Control Variable

The next question should be:

```text
Are these near-boundary states locally action-effective at all?
```

Before designing another objective or training run, M837 should test whether
small direct first-action overrides can change terminal margin on the M832
near-boundary pairs.

This separates:

```text
policy not sensitive enough
```

from:

```text
the selected near-boundary states are not first-action controllable enough
```

The probe should sweep small action directions:

```text
left_to_right_action_delta
negative_left_to_right_delta
steer +/- epsilon
brake +/- epsilon
throttle +/- epsilon
```

and measure whether any bounded override creates:

```text
margin_delta >= 0.01
or success/collision flip
```

If action-effective directions exist, then the next branch can design an
outcome-coupled objective. If not, the data route needs different boundary
states or a longer-horizon action sequence target.

## Decision

Decision:

```text
admit_near_boundary_action_effectiveness_probe_design
```

Next:

```text
m837-v4-near-boundary-action-effectiveness-probe-design
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and threshold relaxation remain blocked.
