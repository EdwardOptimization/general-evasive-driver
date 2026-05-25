# M825 V4 Extreme Hidden-Dynamics Data Route Implementation

## Purpose

M825 implements and runs the no-training data route designed in M824.

The experiment question is:

```text
Can a broader extreme hidden-dynamics route produce source-diverse rows where
command-response history interventions degrade margin or action behavior?
```

M825 is infrastructure/data-route only:

```text
no actor update
no M761 residual-head update
no learned calibrator training
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_extreme_hidden_dynamics_data_route.py
```

New tests:

```text
tests/test_v4_extreme_hidden_dynamics_data_route.py
```

The implementation reuses the M811 source/snapshot/retarget route, but extends
replay with history interventions:

```text
normal
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
command_shift_obs
response_delay_obs
```

`wrong_cross_fault_history` is not faked. M825 logs it as:

```text
unsupported_history_variants: ["wrong_cross_fault_history"]
reason: requires paired hidden-state injection
```

The replay action remains:

```text
action = base_action + 0.2 * residual_M761(features)
```

with a parameter-free identity residual gate. The M568 actor and M761 residual
head are frozen.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_extreme_hidden_dynamics_data_route \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m825_v4_extreme_hidden_dynamics_data_route \
  --device cpu
```

## Result

Run directory:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route
```

Summary:

```text
result_class: v4_extreme_hidden_dynamics_data_route_sparse
fault_specs: 18
source_groups: 64
source_snapshots: 64
candidate_plan_rows: 512
normal_replay_rows: 512
history_intervention_rows: 3072
accepted_self_id_raw_rows: 47
accepted_self_id_rows: 18
accepted_mitigation_raw_rows: 40
accepted_mitigation_rows: 12
matched_pair_rows: 256
history_sensitive_candidate_rows: 47
replay_errors: 0
elapsed_seconds: 35.290913343429565
```

The pre-registered primary self-ID gate required:

```text
min_self_id_rows: 120
```

Balanced M825 found only:

```text
accepted_self_id_rows: 18
```

so the result is sparse and cannot admit PPO, promotion, or a driver-capability
claim.

## Diversity

Accepted self-ID diversity:

```text
rows: 18
unique_seed_count: 2
unique_source_group_count: 3
unique_fault_family_pair_count: 3
unique_fault_family_count: 3
unique_fidelity_class_count: 2
unique_onset_bucket_count: 2
unique_warmup_mode_count: 1
max_seed_dominance: 0.6666666666666666
max_source_group_dominance: 0.3333333333333333
max_fault_family_pair_dominance: 0.3333333333333333
```

Accepted self-ID rows are concentrated in:

```text
fault families: brake_authority_drop, combined_fault, steering_fault
onset buckets: pre_emergency, mid_maneuver
warm-up mode: natural_policy only
```

This concentration is the main reason the data-route pass gate fails.

Matched action-divergent diagnostics:

```text
matched_pair_rows: 256
unique_fault_family_pair_count: 16
unique_fidelity_pair_count: 3
unique_left_fault_family_count: 7
unique_right_fault_family_count: 5
unique_left_warmup_mode_count: 3
unique_right_warmup_mode_count: 3
unique_onset_pair_count: 6
```

These rows are diagnostic matched-current-state/action-divergent proxy pairs.
They are not yet wrong-cross-fault history injections.

## Intervention Signals

Supported intervention counts:

```text
reset_hidden_each_step: 512
reset_hidden_then_normal: 512
zero_command_obs: 512
command_shift_obs: 512
response_delay_obs: 512
wrong_cross_fault_history: 512 unsupported diagnostic rows
```

Maximum normal-minus-intervention margin gaps:

```text
zero_command_obs:       0.028255885109984114
reset_hidden_each_step: 0.012439503461971757
command_shift_obs:      0.005916646036354667
reset_hidden_then_normal: 0.003019702661738677
response_delay_obs:     0.00006529045199066275
```

The strongest accepted rows are driven mainly by `zero_command_obs`, with some
support from `reset_hidden_each_step`. Delayed-response sensitivity is weak in
this run.

## Contract Checks

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

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

## Proxy Boundary

M825 writes:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route/fault_proxy_limitations.md
```

Rows with:

```text
fidelity_class = current_model_proxy
```

are stress proxies only. They are not true single-wheel, split-mu,
stuck-caliper, halfshaft, suspension, or wheel-speed sensor physical dynamics.

## Decision

Decision:

```text
v4_extreme_hidden_dynamics_data_route_sparse
```

Supported claims:

- the M825 no-training route works end-to-end;
- supported reset/zero-command/shifted/delayed history interventions are
  evaluated and logged;
- actor and residual-head parameters are unchanged;
- the route finds some history-sensitive rows, but they are sparse and
  source-concentrated;
- matched action-divergent proxy pairs exist and are worth auditing.

Unsupported claims:

- source-diverse extreme hidden-dynamics self-ID evidence is established;
- wrong-cross-fault history intervention has been implemented;
- delayed-response history is currently a strong signal;
- the route admits PPO, calibration, or checkpoint promotion.

Next:

```text
m826-v4-extreme-hidden-dynamics-data-route-audit
```

M826 should audit whether the sparse result is mainly a sampling budget issue,
a missing wrong-history-injection issue, or evidence that current M568/M761
behavior is not yet strongly response-history sensitive under this route.
