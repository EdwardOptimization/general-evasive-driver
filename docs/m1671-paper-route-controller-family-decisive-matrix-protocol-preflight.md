# M1671 Paper-Route Controller-Family Decisive Matrix Protocol Preflight

## Summary

M1671 implements and runs the no-training protocol preflight admitted by M1670.

Decision:

```text
controller_family_decisive_matrix_protocol_preflight_pass_route_to_audit
```

This milestone creates protocol artifacts only. It does not train, replay,
evaluate policies, run PPO, promote a checkpoint, use private holdout, change
actor inputs, repair the M1663 artifact, or claim controller-family ranking,
paper-level evidence, or level3 self-identification.

## Command

```text
PYTHONPATH=src python -m autodrift.controller_family_decisive_matrix_protocol --output-dir runs/m1671_controller_family_decisive_matrix_protocol
```

## Artifacts

```text
runs/m1671_controller_family_decisive_matrix_protocol/summary.json
runs/m1671_controller_family_decisive_matrix_protocol/matrix_protocol.json
```

## Result

The preflight passed:

```text
result_class: controller_family_decisive_matrix_protocol_preflight_pass
passes_public_smoke_gates: true
profile_config_count: 12
expected_profile_count: 12
missing_profile_names: []
contract_violation_count: 0
guardrail_violation_count: 0
```

Referenced public artifacts are readable:

```text
standard_summary_readable: true
standard_completed_seed_runs: 36
standard_profile_count: 12
standard_private_holdout_used: false
standard_profile_specific_tuning: false

clean_package_summary_readable: true
clean_positive_candidate_count: 39
clean_diagnostic_guardrail_count: 232

artifact_failure_summary_readable: true
artifact_first_check_pass: false
artifact_proof_washout_count: 2
artifact_behavior_regression_count: 2
```

Guardrails stayed false:

```text
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
artifact_repair_started: false
profile_specific_tuning_admitted: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Protocol Contents

`matrix_protocol.json` records the 12 controller profiles:

```text
L0_current_masked
L1_one_step
L2_window_13 / 25 / 50 / 100
L2_window_13 / 25 / 50 / 100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

It also records the evidence layers:

```text
standard_profile_baseline: M1497 aggregate public profile pilot
clean_active_set_package: M1615 39-positive / 232-diagnostic public package
artifact_route_regression_guardrail: M1666 first-check replay failure
```

The protocol preserves the M1670 claim rules:

```text
reactive_negative
finite_window_positive
recurrent_advantage
strong_self_id
```

## Supported Claims

Supported:

```text
the controller-family decisive matrix can be represented as a machine-readable
public protocol;
all 12 corrected profile configs exist and pass basic P0/no-oracle guardrails;
the standard baseline, clean package, and artifact-regression summaries are
available for the next audit;
the next step can be an audit of the protocol before any one-seed public pilot.
```

## Unsupported Claims

Unsupported:

```text
controller-family ranking;
decisive-task training readiness;
one-seed or three-seed matrix performance;
private-holdout generalization;
checkpoint promotion;
paper-level evidence;
level3 self-identification.
```

## Decision

Route to a process audit before any pilot:

```text
m1672-paper-route-controller-family-decisive-matrix-protocol-preflight-result-audit
```

M1672 should decide whether the protocol is ready for one-seed public plumbing
pilot design, or whether the mapping from clean active-set package to
controller-family tasks needs repair first.

## Guardrails

```text
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1672-paper-route-controller-family-decisive-matrix-protocol-preflight-result-audit
```
