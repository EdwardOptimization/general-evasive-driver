# M1536 Paper-Route Fresh Ambiguity History-Intervention Repeat Design

## Summary

M1536 designs the source-expanded repeat admitted by M1535.

Decision:

```text
fresh_ambiguity_history_intervention_repeat_design_admit_bounded_implementation
```

M1534 produced promising wrong-history and donor-response/action-plus-hidden
margin gaps, but the evidence was source-small, T4-only, and dominated by
reset/zero-current controls. M1536 therefore does not materialize candidates or
claim self-identification. It pre-registers a repeat that must expand source
scope before any training corpus, PPO, promotion, private holdout, or paper-level
claim is allowed.

## Inputs

Use the same deployable actor contract and public checkpoint:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

actor contract:
  P0 human-view no-wheel 72-dim frame with online GRU hidden state

source families:
  all 14 fresh ambiguity source families from M1527/M1528

holdout policy:
  public development repeat only
```

Privileged simulator metadata may be logged for mining, filtering, and audit.
It must not enter actor observation, actor hidden state, or deployed action
logic.

## Repeat Scope

The post-synthesis implementation should run a two-stage bounded repeat:

```text
Stage A: source-expanded measured mining
Stage B: history interventions over accepted measured pairs from Stage A
```

Use a fresh public seed namespace rather than reusing M1531:

```text
source_seed: 1631
source_seed_count: 2
expected source rows: 28
max_pair_candidates: 128
continuation_steps: 64
```

The implementation command should be:

```text
PYTHONPATH=src python -m autodrift.fresh_ambiguity_measured_mining \
  --output-dir runs/m1538_fresh_ambiguity_measured_mining_repeat \
  --seed 1631 \
  --seed-count 2 \
  --max-pair-candidates 128

PYTHONPATH=src python -m autodrift.fresh_ambiguity_history_interventions \
  --output-dir runs/m1538_fresh_ambiguity_history_intervention_repeat \
  --pair-candidates runs/m1538_fresh_ambiguity_measured_mining_repeat/measured_pair_candidates.csv \
  --source-seed 1631 \
  --source-seed-count 2 \
  --continuation-steps 64
```

## Required Intervention Channels

The repeat must preserve every M1534 channel:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
donor_response_action_plus_hidden_from_anchor
```

The audit must keep these evidence classes separate:

```text
wrong-history hidden sensitivity
donor response/action stream sensitivity
donor response/action plus hidden sensitivity
delayed hidden sensitivity
reset/zero-current positive controls
success-drop or collision outcome changes
```

## Source-Diversity Gates

The repeat artifacts should pass these public repeat gates before any stronger
route is considered:

```text
source_row_count >= 28
attempted_source_families >= 14
reached_decision_source_families >= 12
accepted_measured_pair_count >= 6
accepted_source_family_edge_count >= 5
max_accepted_source_family_share <= 0.50
anchor_replay_failure_rate <= 0.05
guardrail_violation_count == 0
```

If `accepted_measured_pair_count < 6`, classify the result as
`scenario_sampling_failure` or `source_pairing_failure` and route to pair repair,
not materialization.

## T5 / Terminal-Boundary Handling

M1534 accepted only T4 pairs. The repeat must report:

```text
t5_or_terminal_boundary_accepted_pair_count
t5_or_terminal_boundary_history_positive_count
t5_or_terminal_boundary_anchor_failure_count
```

Preferred pass condition:

```text
t5_or_terminal_boundary_accepted_pair_count >= 1
```

If no T5 or terminal-boundary pair is accepted but other source-diversity gates
pass, the run may still be a source-expanded T4 repeat. It cannot support
candidate materialization. The follow-up audit must choose between:

```text
task generation / retargeting for terminal-boundary rows
pair repair for near-boundary acceptance
branch synthesis if history effects remain T4-only
```

## History-Sensitivity Gates

The repeat should report positive history sensitivity only if at least one of
these conditions holds:

```text
wrong_history_positive_pair_count >= 2
wrong_history_positive_source_edge_count >= 2

or

donor_plus_hidden_positive_pair_count >= 2
donor_plus_hidden_positive_source_edge_count >= 2

or

wrong_or_donor_success_drop_count >= 1
```

Positive means:

```text
terminal_margin_gap_from_normal >= 0.02
```

Action-only changes without terminal-margin or outcome changes are diagnostic
only. They do not admit materialization.

## Control-Dominance Rule

M1534 showed stronger reset/zero-current effects than wrong-history effects.
The repeat must therefore compute:

```text
max_reset_zero_margin_gap
max_wrong_history_margin_gap
max_donor_plus_hidden_margin_gap
control_to_history_gap_ratio
```

If controls exceed history interventions by more than `4x` and history positives
are not source-diverse, the result is a current-response/control-sensitivity
finding, not self-identification evidence.

## Materialization Rule

The repeat implementation cannot materialize candidates. Even if the repeat
passes, the next step after implementation must be an audit:

```text
m1539-paper-route-fresh-ambiguity-history-intervention-repeat-result-audit
```

Candidate materialization requires a later design milestone that explicitly
names:

```text
candidate selection criteria
source-family caps
training use
proof/generalization split
private-holdout policy
failure taxonomy
anti-overfitting controls
```

## Failure Taxonomy

Use these labels in the repeat implementation and follow-up audit:

```text
none
scenario_sampling_failure
source_pairing_failure
anchor_replay_failure
history_effect_null
control_dominance
t5_absent
metric_artifact
contract_violation
```

If the validator does not yet allow a needed label, the implementation must
either use the nearest existing label or extend the taxonomy with tests before
relying on it.

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
m1537-paper-route-fresh-ambiguity-source-mining-branch-synthesis
```
