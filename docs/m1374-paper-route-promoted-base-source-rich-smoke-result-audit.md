# M1374 Paper-Route Promoted-Base Source-Rich Smoke Result Audit

## Purpose

M1374 audits the M1373 source-rich smoke before routing to any larger public
source-rich wave, L0/L1/L2/L3 comparison refresh, PPO continuation, promotion,
or private-holdout use.

M1374 does not train, run PPO, run new evaluation, promote, use private holdout,
change actor inputs, or make high-fidelity physical claims.

## M1373 Evidence

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

M1373 artifact:

```text
runs/m1373_promoted_base_source_rich_smoke/summary.json
```

M1373 result:

```text
result_class: cross_fault_wrong_sparse
scenario_count: 832
snapshot_count: 3289
matched_pair_count: 768
unmatched_rows: 0
accepted_rows: 2
reset_only_rows: 174
rejected_rows: 592
normal_failed_rejected: 184
history_insensitive_rejected: 408
wrong_history_action_critical_rows: 2
reset_history_action_critical_rows: 174
unique_accepted_fault_families: 2
unique_accepted_wrong_fault_families: 2
unique_accepted_severities: 2
unique_accepted_seeds: 1
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The smoke passes the M1372 structural gate. It produced positive scenario,
snapshot, pair, intervention, accepted-row, reset-only, rejected-row, and
fidelity-limit artifacts with no checkpoint mutation or training.

## Accepted-Row Audit

The two accepted rows are diagnostic but narrow:

```text
accepted_rows: 2
unique_accepted_seeds: 1
success_drop rows: 0
accepted fault-family pairs:
  brake_authority_drop->global_mu_drop
  mass_cg_shift->brake_authority_drop
```

M1373 therefore does not prove source-diverse cross-fault wrong-history
self-identification. The correct classification is:

```text
sparse wrong-history diagnostic signal
```

The rows are useful enough to justify a larger public source-rich wave, but not
useful enough to justify objective training, PPO, promotion, private holdout, or
claim expansion.

## Reset-Only Audit

M1373 has broad reset-hidden sensitivity:

```text
reset_only_rows: 174
reset_history_action_critical_rows: 174
reset-positive fault-family pair groups: 11 / 15
```

This supports a weaker claim:

```text
the recurrent state matters under source-rich capability-step faults.
```

It does not support:

```text
wrong-history belief mismatch proof;
source-diverse online self-identification;
level3 anticipatory recurrent belief.
```

Reset-only rows should be preserved as a useful diagnostic axis. If a larger
public wave again yields sparse or zero accepted wrong-history rows, the next
route should be temporal/sequence intervention design rather than direct
training.

## Claim Boundary Audit

M1373 used current single-track and axle-level fault families:

```text
brake_authority_drop
combined_fault
delay_noise_fault
drive_authority_drop
front_lateral_authority_drop
global_mu_drop
mass_cg_shift
rear_lateral_authority_drop
steering_fault
```

The run did not execute faithful future-only physics:

```text
true single-wheel puncture or blowout
true single-corner grip collapse
left-right split-mu
stuck caliper or single-wheel brake pull
single-wheel brake pressure loss
asymmetric half-shaft or CV torque loss
open or locked differential failure
per-wheel ABS fault
wheel-speed sensor failure as physical wheel dynamics
corner suspension or toe damage
tire pressure, temperature, wear, or delamination dynamics
```

This boundary is acceptable. M1375 must keep the same interpretation.

## Route Decision

M1374 admits a larger no-training public source-rich wave:

```text
m1375-paper-route-promoted-base-source-rich-public-wave
```

Reason:

```text
M1373 is structurally clean and has nonzero wrong-history accepted rows, but the
accepted signal is one-seed sparse. The next evidence question is whether that
signal repeats under larger fresh public coverage, not whether the checkpoint is
ready for training or promotion.
```

M1375 should use the existing audited larger-wave config:

```text
configs/m991_capability_step_fault_source_wave.json
```

Planned command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --pairing-mode cross_fault \
  --seed-start 137500 \
  --seed-count 256 \
  --device auto \
  --run-dir runs/m1375_promoted_base_source_rich_public_wave
```

M1375 remains a no-training public evaluation wave. It must not promote, run PPO,
use private holdout, change actor inputs, or convert proxy faults into
high-fidelity claims.

## M1375 Interpretation Rules

M1375 pass/fail should remain structural:

```text
summary exists
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
pairing_mode == cross_fault
model_fidelity_limits.md exists
```

Scientific interpretation:

```text
accepted_rows >= 40, unique_accepted_fault_families >= 4, and
unique_accepted_seeds >= 24:
  source-positive candidate, still requires audit before objective or training.

accepted_rows > 0 but below source-positive thresholds:
  sparse diagnostic signal, route to audit or retargeted intervention design.

accepted_rows == 0 and reset_only_rows high:
  reset-only recurrent-state sensitivity, route to temporal/sequence
  intervention design.

both accepted_rows and reset_only_rows low:
  source-rich current config is weak for history-dependence mining; route to
  source-distribution redesign or simulator capability audit.
```

M1375 should not relax thresholds after seeing the result.

## Supported Claims

M1374 supports:

```text
1. M1373 is a structurally clean promoted-base source-rich smoke.
2. M1373 wrong-history accepted evidence is sparse and diagnostic only.
3. M1373 reset-only evidence is broad and worth preserving.
4. A larger public source-rich wave is the next appropriate evidence step.
```

## Unsupported Claims

M1374 does not support:

```text
1. source-diverse cross-fault self-identification;
2. source-rich promotion;
3. private holdout or paper-level evidence;
4. PPO continuation readiness;
5. L0/L1/L2/L3 comparison conclusions;
6. high-fidelity per-wheel or real-vehicle transfer claims;
7. level3 anticipatory recurrent-belief self-identification.
```

## Decision

Decision:

```text
promoted_base_source_rich_smoke_audit_admit_public_wave
```

Next:

```text
m1375-paper-route-promoted-base-source-rich-public-wave
```
