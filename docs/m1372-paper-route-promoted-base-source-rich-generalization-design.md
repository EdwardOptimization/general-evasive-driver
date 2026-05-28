# M1372 Paper-Route Promoted-Base Source-Rich Generalization Design

## Purpose

M1372 designs the first source-rich public generalization gate after M1370
promoted M1362 alpha `0.1` as the current public-gate base.

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

This milestone is design only. It does not train, run PPO, run source-rich
evaluation, promote a checkpoint, use private holdout, change actor inputs, or
expand the physics claim.

## Design Decision

Admit a no-training promoted-base source-rich smoke:

```text
m1373-paper-route-promoted-base-source-rich-smoke
```

The immediate goal is not to prove source-rich self-identification. It is to
verify that the promoted M1362 base can be run through the existing
capability-step/cross-fault harness with clean artifacts, fixed claim
boundaries, and no private-holdout contamination.

M1373 should use the current capability-step fault config because it is the
smallest already audited source-rich harness that produces scenario, pair, and
intervention artifacts:

```text
configs/m990_capability_step_fault_scenarios.json
src/autodrift/extreme_dynamics_scenario_corpus.py
```

Planned command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m990_capability_step_fault_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 137300 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m1373_promoted_base_source_rich_smoke
```

## Claim Boundary

The existing source-rich harness supports current single-track and axle-level
capability faults only. M1373 and the next source-rich public gates may claim
stress coverage for:

```text
nominal
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
delay_noise_fault
combined_fault
```

The `fidelity_class` field must be preserved in all interpretation:

```text
current_model_fault:
  directly represented by current VehicleParams changes.

current_model_proxy:
  useful as capability-loss stress or self-ID mining proxy, but not physical
  proof of asymmetric wheel-level faults.

future_four_wheel_or_high_fidelity:
  blocked until a four-wheel/contact-patch or higher-fidelity dynamics engine
  exists.
```

Future-only or high-fidelity physical claims remain blocked:

```text
true single-wheel puncture or blowout
true single-corner grip collapse
true left-right split-mu
stuck caliper or single-wheel brake pull
single-wheel brake pressure loss
asymmetric half-shaft or CV torque loss
open or locked differential failure
per-wheel ABS fault
wheel-speed sensor failure as physical wheel dynamics
corner suspension or toe damage
tire pressure, temperature, wear, or delamination dynamics
road crown, bank, or curb-induced per-wheel load asymmetry
```

Those can remain in config metadata or future-roadmap docs, but they are not
executed as faithful physical scenarios by the current single-track model.

## M1373 Gate Semantics

M1373 is a source-rich public smoke gate, not a promotion gate and not a paper
result.

Required artifacts:

```text
runs/m1373_promoted_base_source_rich_smoke/summary.json
runs/m1373_promoted_base_source_rich_smoke/scenario_summary.csv
runs/m1373_promoted_base_source_rich_smoke/fault_family_summary.csv
runs/m1373_promoted_base_source_rich_smoke/fault_family_pair_summary.csv
runs/m1373_promoted_base_source_rich_smoke/severity_summary.csv
runs/m1373_promoted_base_source_rich_smoke/severity_pair_summary.csv
runs/m1373_promoted_base_source_rich_smoke/cross_fault_pair_summary.csv
runs/m1373_promoted_base_source_rich_smoke/matched_hidden_condition_pairs.csv
runs/m1373_promoted_base_source_rich_smoke/matched_cross_fault_pairs.csv
runs/m1373_promoted_base_source_rich_smoke/intervention_rollouts.csv
runs/m1373_promoted_base_source_rich_smoke/accepted_rows.csv
runs/m1373_promoted_base_source_rich_smoke/reset_only_rows.csv
runs/m1373_promoted_base_source_rich_smoke/rejected_rows.csv
runs/m1373_promoted_base_source_rich_smoke/model_fidelity_limits.md
```

Pass conditions:

```text
summary.json exists
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
pairing_mode == cross_fault
private_holdout_used is absent or false
current_model_fault_families contains at least three executable families
model_fidelity_limits.md exists
scenario and pair summaries are finite and readable
```

Non-pass conditions:

```text
training, PPO, checkpoint promotion, or actor-input mutation occurs
private holdout is used
future-only high-fidelity faults are reported as executed physical claims
summary or core CSV artifacts are missing
no scenarios, snapshots, or matched pairs are produced
```

Source-positive counts are metrics, not smoke pass requirements:

```text
accepted_rows
reset_only_rows
wrong_history_action_critical_rows
reset_history_action_critical_rows
unique_accepted_fault_families
unique_accepted_severities
unique_accepted_seeds
```

Zero accepted wrong-history rows is not a gate failure for M1373. Prior
capability-step work showed that cross-fault wrong-history positives can be
sparse even when temporal/reset sensitivity exists. M1373 must classify such an
outcome as a source-sampling result or negative evidence, not as a reason to
relax thresholds or overclaim.

## Metrics To Preserve

M1373 should record at least:

```text
scenario_count
snapshot_count
matched_pair_count
unmatched_rows
accepted_rows
reset_only_rows
rejected_rows
normal_failed_rejected
history_insensitive_rejected
history_action_critical_rows
wrong_history_action_critical_rows
reset_history_action_critical_rows
unique_accepted_fault_families
unique_accepted_wrong_fault_families
unique_accepted_severities
unique_accepted_seeds
current_model_fault_families
future_only_fault_families
actor_parameters_changed
training_started
ppo_used
promoted
result_class
```

The audit should also read the family-pair and severity-pair CSVs before making
any conclusion about source diversity. A nonzero `accepted_rows` value from one
seed, one severity, or one family pair remains narrow diagnostic signal.

## Ordering Relative To L0/L1/L2/L3

M1372 keeps the paper-route ordering explicit:

```text
1. Run promoted-base source-rich public smoke on the current L3 public base.
2. Audit whether the source-rich harness produces clean artifacts and meaningful
   public stress metrics.
3. If the smoke passes structurally, run a larger public source-rich wave.
4. Only after the source-rich public distribution is fixed, refresh the fair
   L0/L1/L2/L3 comparison protocol.
5. Train or evaluate L0/L1/L2/L3 under fixed budgets and fixed source-rich
   evaluation sets without per-profile tuning.
6. Use private holdout only after public protocol stabilization, and rotate it
   if it guides repair.
```

L0/L1/L2/L3 claims must remain separate:

```text
L0:
  current-only feedback.

L1:
  one-step feedback with previous command and actuator state.

L2:
  finite-window command-response history.

L3:
  GRU recurrent history.
```

If L2 finite-window matches or beats L3 on fixed public and holdout
distributions, the project should not claim a recurrent-belief advantage. If L3
only wins in current-ambiguous or older-history-dependent scenarios, the claim
must be scoped to those scenarios.

## Next Route

M1373 should run the promoted-base source-rich smoke above.

Likely follow-up after M1373:

```text
M1374:
  audit M1373 and decide whether to scale to a larger public source-rich wave.

M1375 or later:
  run larger source-rich public wave using a fixed config before any
  private-holdout use or L0/L1/L2/L3 retraining.

Fair-comparison refresh:
  design L0/L1/L2/L3 comparison only after the public source-rich distribution
  and metrics are stable.
```

Do not route directly from M1372 to PPO continuation, private holdout, paper
claims, or high-fidelity simulator migration.

## Decision

M1372 passes as a process/design milestone.

Decision:

```text
promoted_base_source_rich_generalization_design_admit_smoke
```

Next:

```text
m1373-paper-route-promoted-base-source-rich-smoke
```
