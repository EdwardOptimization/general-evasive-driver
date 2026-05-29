# M1520 Paper-Route Decisive History Bounded Runner Synthesis

## Summary

M1520 synthesizes the bounded-runner branch from M1510 through M1519.

Decision:

```text
decisive_history_bounded_runner_synthesis_promote_to_timing_amplified_branch
```

Synthesis decision:

```text
promote_to_next_branch
```

The branch built reliable bounded fixed-policy trace, retarget, and intervention
plumbing. It also produced an important negative result: the first T5
decision-step intervention smoke did not show outcome-relevant history
sensitivity. The best next step is not another narrow tweak inside the same
branch. It is a new bounded branch for timing-amplified interventions, starting
from the M1519 design.

No candidate materialization, corpus export, training, PPO, promotion, private
holdout, actor-input change, or level3 self-identification claim is admitted by
this synthesis.

## Evidence Summary

### Bounded Runner

M1510 designed a fixed-policy source trace runner with public checkpoint,
source-family caps, trace schemas, and materialization guardrails.

M1511 implemented the runner:

```text
spec/source_family_count: 6/6
trace_row_count: 525
snapshot_row_count: 30
rollout_success/failure_count: 6/0
source families reached reveal/decision/post_decision: 6/6/6
guardrail_violation_count: 0
```

M1512 audited those traces as clean plumbing but not candidate evidence:

```text
min_trace_margin: 4.170293752717424
label issue: five of six source families were aeb_feasible
candidate_materialization_verdict: not_admissible_yet
```

### Source Retarget

M1513 designed bounded public retargeting to reduce margins and improve label
diversity.

M1514 implemented the retarget smoke:

```text
spec/source_family/retarget_mode_count: 24/6/4
trace_row_count: 1576
snapshot_row_count: 95
rollout_success/failure_count: 19/5
failure_type_counts: reset_failure=4, did_not_reach_decision_step=1
global_min_margin: -0.042059208331689746
near_boundary_proxy_count: 39
non_aeb_label_source_family_count: 2
guardrail_violation_count: 0
```

M1515 audited the retarget result and admitted only the
`t5_high_speed_close_obstacle` subset to measured intervention design:

```text
eligible_modes: close_wide, low_mu_close, late_reveal_high_speed, drift_required_focus
eligible_min_margin: 0.23423498489590822
candidate_materialization_verdict: blocked
```

### Decision-Step T5 Interventions

M1516 designed bounded normal/reset/zero/delayed/wrong-donor interventions for
the admitted T5 subset.

M1517 implemented and ran the smoke:

```text
eligible_target_count: 4
variant_count: 7
intervention_row_count: 28
target/donor replay failure count: 0/0
max_margin_gap_from_normal: 0.016497911642290308
outcome_relevant_variant_count: 0
success_drop_count: 0
guardrail_violation_count: 0
```

M1518 audited that result:

```text
largest_effect_variant: reset_hidden_every_step on low_mu_close
mean_reset_hidden_every_step_gap: 0.008551990884898553
mean_wrong_history_donor_hidden_gap: 0.0000036857291120240276
mean_zero_action_history_gap: -0.00011307254624004504
failure_types: scenario_sampling_failure, metric_artifact
```

The audit separated action sensitivity from outcome relevance. Reset-hidden
changed actions but the rows absorbed the change. Wrong-donor hidden, delayed
hidden, and zero action history were near-null at the decision-step injection
point.

### Timing-Amplified Design

M1519 designed an earlier-window intervention route:

```text
anchors: decision, decision_minus_8, reveal_plus_4, reveal
variants: normal, reset_hidden_once_at_anchor,
          reset_hidden_every_step_from_anchor,
          zero_current_response_from_anchor,
          zero_action_history_from_anchor,
          delayed_hidden_8_at_anchor,
          wrong_history_donor_hidden_at_anchor
primary threshold: success_drop_from_normal or margin_gap_from_normal >= 0.02
secondary diagnostic: decision-state divergence or post-anchor action L2
```

M1519 correctly separates same-current diagnostics from diverging-trajectory
timing interventions. That matters because earlier interventions can change the
physical setup before decision; a positive result would justify stronger mining
but would still need audit before self-identification claims.

## Supported Claims

The branch supports these claims:

```text
bounded public fixed-policy trace collection works for current T4/T5 source
families;

retargeting can move scenarios from very high-margin to near-boundary or
failure conditions;

the T5 high-speed subset can be replayed deterministically enough for bounded
measured interventions;

decision-step intervention plumbing works and records null effects cleanly;

M1519 defines a feasible next test that starts interventions earlier and
separates same-current from diverging-trajectory interpretations.
```

## Falsified Or Unsupported Claims

The branch does not support:

```text
M1511 default source traces are decisive-history candidates;

M1517 decision-step interventions prove history necessity;

wrong-donor hidden at the decision step causes outcome degradation;

the admitted T5 subset is ready for candidate materialization;

training corpus export;

policy superiority;

level3 anticipatory self-identification.
```

The decision-step intervention route is specifically falsified as sufficient
evidence for candidate materialization.

## Failure Taxonomy Summary

Observed failure labels:

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` appears in two forms:

```text
M1511 traces were too safe, with min margin 4.17 m;
M1517 decision-step interventions had enough slack that action changes did not
create outcome drops.
```

`metric_artifact` risk is active because several infrastructure milestones
produce clean artifacts, but clean artifacts are not evidence of history
necessity.

M1514 also exposed bounded retarget failures:

```text
reset_failure
did_not_reach_decision_step
```

No actor-input contract violation, private holdout contamination, promotion
gate misuse, training instability, or PPO washout occurred in this branch.

## Public-Gate Overfit Risk

Risk:

```text
medium_high
```

Reasons:

```text
the branch repeatedly used the same public checkpoint;
M1517/M1518 focused on only four admitted T5 high-speed rows;
the public T5 subset has already shaped the next intervention design;
no private holdout was used, by design.
```

This is acceptable for infrastructure and probe design, but not for paper-level
evidence or promotion. Any future positive timing-amplified result must be
audited and then generalized to fresh rows before it becomes a training or paper
claim.

## Next Branch Decision

Promote to a new branch:

```text
paper_route_t5_timing_amplified_intervention
```

Admit exactly one bounded implementation from the M1519 design:

```text
m1521-paper-route-t5-timing-amplified-intervention-implementation
```

The new branch must keep these constraints:

```text
public checkpoint only;
four admitted T5 high-speed targets only unless a manifest expands scope;
no candidate materialization;
no corpus export;
no training;
no PPO;
no private holdout;
no actor-input change;
no self-ID claim from plumbing alone.
```

Hard follow-up rule:

```text
implementation -> mandatory audit.
```

If timing amplification produces outcome-relevant gaps, audit before any corpus
export or candidate materialization. If it produces only state/action divergence,
pivot to terminal-boundary retarget repair. If it is null across action, state,
and outcome, close the current T5 subset or synthesize before further T5 tweaks.

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

## Next

```text
m1521-paper-route-t5-timing-amplified-intervention-implementation
```
