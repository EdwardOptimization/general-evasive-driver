# M1281 Paper-Route Four-Wheel Source Response-History Materialization Result Audit

## Summary

M1281 audits the M1280 source response-history artifacts before any policy-side
use.

Decision:

```text
four_wheel_source_response_history_audit_admit_policy_gate_design
```

M1280 is artifact-clean and distinguishable enough for the next design step:

```text
history_prefix_rows: 152
history_frame_rows: 3648
history_intervention_rows: 152
wrong_history_pair_rows: 152
wrong_history_valid_count: 152
```

The artifacts still do not prove self-identification. They only create a clean
source substrate where a future policy-side gate can compare correct history
against same-pair wrong history under the same current intervention state.

## Evidence

Primary artifacts:

```text
runs/m1280_four_wheel_source_response_history_materialization/summary.json
runs/m1280_four_wheel_source_response_history_materialization/history_prefix_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/history_frame_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/history_intervention_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/wrong_history_pair_rows.csv
```

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

No training, PPO, checkpoint promotion, private holdout, threshold relaxation,
actor-input expansion, driver-performance claim, paper-level claim, or
self-identification claim occurs in M1281.

## Artifact Shape

M1280 produced:

```text
unique source pairs: 38
unique interventions: 76
history prefixes per intervention: 2
history frames per prefix: 24
history prefix rows: 152
history frame rows: 3648
history intervention rows: 152
wrong history pair rows: 152
```

Coverage by source family:

```text
single_wheel_grip_collapse: 84 history prefixes
left_right_split_mu: 60 history prefixes
single_wheel_brake_pull: 8 history prefixes
```

Coverage by condition and probe:

```text
condition A: 76
condition B: 76
left_brake_probe: 76
right_brake_probe: 76
```

Interpretation:

```text
The artifacts are balanced across branch condition and probe template. Family
coverage is inherited from the M1277 near/high union subset, so brake-pull is
present but thin.
```

## History Cleanliness

The actor-view history fields are finite:

```text
actor_view_history_column_count: 15
actor_view_history_all_finite: true
forbidden_actor_view_history_columns: []
```

The actor-view history columns are:

```text
cmd_steer
cmd_throttle
cmd_brake
vx
vy
yaw_rate
ax
ay
steer_state
steer_rate
drive_state
brake_state
prev_cmd_steer
prev_cmd_throttle
prev_cmd_brake
```

Artifact metadata columns also exist in `history_frame_rows.csv`:

```text
history_id
pair_id
condition
fault_name
fault_family
probe_template
step
```

Those metadata columns are not deployable actor inputs. They are allowed for
audit and pairing only.

Important policy-side caveat:

```text
The canonical 72-value actor frame uses response indices 0-11:
vx, vy, yaw_rate, ax, ay, steer_state, steer_rate,
drive_state, brake_state, prev_cmd_steer, prev_cmd_throttle, prev_cmd_brake.
```

Therefore `cmd_steer`, `cmd_throttle`, and `cmd_brake` must be treated as
prefix action metadata, not appended as additional policy observation channels.
The next policy-side gate must explicitly project M1280 rows into canonical
72-value frames and must normalize the response stream according to
`docs/observation-contract.md`.

## Response Distinguishability

Branch response diagnostics:

```text
response_l2_min: 0.0157835288
response_l2_p10: 0.1733337990
response_l2_median: 0.2204658044
response_l2_p90: 0.2621302766
response_l2_max: 0.2621302766
response_l2_mean: 0.2109745544
response_l2_ge_0_01_count: 152 / 152
```

Yaw-rate and lateral-velocity branch differences:

```text
final_yaw_rate_diff_min: 0.0561069872
final_yaw_rate_diff_median: 0.1323953987
final_yaw_rate_diff_ge_0_01_count: 152 / 152

final_vy_diff_min: 0.0028926375
final_vy_diff_median: 0.3357409229
final_vy_diff_ge_0_01_count: 144 / 152
```

Interpretation:

```text
Every prefix has measurable aggregate response separation and every prefix has
yaw-rate separation above 0.01. Lateral-velocity separation is weaker for eight
prefixes, but the aggregate response and yaw signals remain nonzero.
```

This is enough to design a policy-side correct-history versus wrong-history
gate. It is not enough to claim that any current actor uses that history.

## Wrong-History Semantics

Wrong-history rows satisfy the intended swap semantics:

```text
wrong_history_pair_rows: 152
same_pair_swap true: 152
opposite_condition_swap true: 152
wrong_history_valid_count: 152
correct_history_id != wrong_history_id: 152
```

Each intervention has two linked histories:

```text
interventions with 2 history links: 76
correct history link count per prefix: 1
history frame count per prefix: 24
```

This means the future gate can compare:

```text
same source pair;
same current intervention observation;
same preferred/rejected action relation;
correct branch response history versus opposite-branch wrong history.
```

## Intervention Outcome Context

The M1280 histories attach to the M1277 near/high union interventions:

```text
history_intervention_rows: 152
margin_gap_min: 0.0242185615
margin_gap_p10: 0.0307991908
margin_gap_median: 0.0925762022
margin_gap_p90: 0.5089764517
margin_gap_max: 0.8165994033
margin_gap_mean: 0.1755786930
```

Interpretation:

```text
The intervention rows have nontrivial preferred/rejected outcome gaps, so a
future policy-side gate can ask whether correct history makes preferred actions
more likely than wrong-history actions.
```

## Readiness And Limits

Ready for:

```text
policy-side source-history gate design;
canonical 72-frame projection design;
correct-history versus wrong-history action-likelihood/action-distance probe
design;
future no-training implementation of that gate.
```

Not ready for:

```text
direct behavior cloning;
PPO;
checkpoint promotion;
private holdout evaluation;
paper-level result claims;
high-fidelity vehicle claims;
self-identification claims.
```

The key remaining gap is policy-side semantics. M1280 proves that response
histories exist and are cleanly pairable. It does not prove that the current
GRU actor maps those histories into different or correct actions.

## Next Step

Admit design-only:

```text
m1282-paper-route-source-history-policy-gate-design
```

M1282 should design a no-training gate that:

```text
projects M1280 history frames into canonical 72-value actor frames;
normalizes response indices according to the observation contract;
replays correct-history and wrong-history prefixes through a recurrent actor;
evaluates preferred/rejected action likelihood or action distance at the same
current intervention observation;
reports whether a policy is history-sensitive on this source corpus;
keeps all fault/condition/pair labels out of actor inputs;
does not train, run PPO, promote, or use private holdout.
```

The expected result is a gate design, not a driver result.

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into Gym yet.

Route to:

```text
experiments/manifests/m1282-paper-route-source-history-policy-gate-design.json
```
