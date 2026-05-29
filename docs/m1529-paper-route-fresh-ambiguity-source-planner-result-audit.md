# M1529 Paper-Route Fresh Ambiguity Source-Planner Result Audit

## Summary

M1529 audits the M1528 dry source-planner smoke.

Decision:

```text
fresh_ambiguity_source_planner_audit_admit_measured_mining_design
```

The M1528 planner is source-diverse and guardrail-clean enough to admit a
measured public source-mining design. It is not enough to materialize
candidates, export a corpus, train, run PPO, promote, use private holdout, or
claim self-identification.

## Audited Evidence

Artifact:

```text
runs/m1528_fresh_ambiguity_source_planner_smoke/summary.json
```

Key results:

```text
source_plan_count: 14
generated_source_specs: 112
accepted_pair_candidates: 112
unique_source_families: 14
unique_hidden_capability_pairs: 24
unique_geometry_keys: 42
unique_decision_steps: 20
max_single_source_family_share: 0.07142857142857142
closed_t5_subset_rows: 0
max_closed_t5_subset_share: 0.0
proxy_fault_family_count: 7
symmetric_proxy_fault_only: true
guardrail_violation_count: 0
passes_public_dry_gates: true
```

Guardrails:

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

## Verdicts

### Source Diversity

Verdict:

```text
pass_for_measured_design
```

Reasons:

```text
14 source families;
112 planned source rows;
24 hidden capability pairs;
42 geometry keys;
20 decision steps;
max single source-family share 0.0714;
closed four-row T5 subset share 0.0.
```

This is sufficient for a measured public source-mining design.

### Proxy-Fault Semantics

Verdict:

```text
pass_with_scope_boundary
```

The planner uses seven proxy-fault families:

```text
actuator_delay_step
brake_fade_or_loss_proxy
capability_step_down
capability_step_up
drive_loss_proxy
grip_loss_proxy
t4_actuator_delay_response
```

They are explicitly scoped as symmetric single-track capability proxies. This
must remain true until the simulator actually models asymmetric wheel/axle
failure. The project must not describe these rows as true one-wheel blowout,
split-mu, half-shaft, or individual-wheel-drive failures.

### Guardrails

Verdict:

```text
pass
```

No training, PPO, replay, private holdout, promotion, actor-input change,
candidate materialization, corpus export, or label-to-actor leakage occurred.

### Evidence Claim

Verdict:

```text
planner_ready_not_self_id_evidence
```

M1528 rows are planned metadata rows. Their distances and action-divergence
fields are planned targets, not measured rollout facts. Therefore M1528 supports
only:

```text
we now have a source-diverse public grid ready for measured mining.
```

It does not support:

```text
the policy uses history;
wrong history changes outcome;
candidate rows are materializable;
the driver is better than baselines;
paper-level self-identification evidence.
```

## Risk Assessment

Main residual risks:

```text
planned ambiguity may not survive actual rollout;
fixed policy may not reach comparable scene/current states for all families;
action-divergence values may shrink once measured instead of planned;
near-boundary rows may be too easy or too unstable;
proxy-fault labels may be overinterpreted if documentation drifts.
```

These risks require measured mining before candidate materialization.

## Next Route

Admit design of measured public source mining:

```text
m1530-paper-route-fresh-ambiguity-measured-mining-design
```

M1530 should design the measured runner that:

```text
uses M1528 source specs;
runs fixed-policy public traces only;
records reveal/reveal_plus_4/decision_minus_8/decision/post_decision windows;
pairs rows by measured scene/current-state distances;
measures action divergence and terminal margin sensitivity;
writes accepted and rejected measured pair artifacts;
keeps candidate materialization and corpus export blocked until a later audit.
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

## Next

```text
m1530-paper-route-fresh-ambiguity-measured-mining-design
```
