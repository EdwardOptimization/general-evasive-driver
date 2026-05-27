# M1070 V4 Public Base Medium PPO Proof-Washout Audit

## Purpose

M1070 audits the M1069 medium-ramp PPO failure before any new PPO proposal.
It only reads M1069 artifacts. It does not train, run PPO, promote, or use
private holdout.

## Inputs

```text
base_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
raw_checkpoint: runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
summary: runs/m1069_expanded_gate_medium_ppo_seed61069/summary.json
exact: runs/m1069_expanded_gate_medium_ppo_seed61069/exact_contract_summary.csv
old_replay: runs/m1069_expanded_gate_medium_ppo_seed61069/proof_replay_summary.csv
family: runs/m1069_expanded_gate_medium_ppo_seed61069/family_intersection_summary.json
source_diverse: runs/m1069_expanded_gate_medium_ppo_seed61069/source_diverse_summary.json
```

## Top-Level Classification

```text
ppo_returncode: 0
training_metrics_finite: true
actor_inputs_changed: false
exact_pass: false
public_replay_pass: false
family_intersection_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
failure_type: proof_washout
```

This is not a training-instability, actor-contract, broad-generalization, or
behavior-regression failure. It is a proof-retention failure: the raw 8192-step
PPO proposal keeps normal-history behavior good enough for broad gates, but
makes several wrong-history rollouts marginally successful.

## Exact Gate Localization

The exact contract failed before replay gates:

```text
full_exact_contract_gate_pass: false
m297_m270_exact_pass: true
exact_m297_delta_vs_base: 0.0
exact_m270_delta_vs_base: 0.0
combined_anchor_total_loss: 0.0000188576
combined_anchor_m267_loss: 0.0000558008
combined_anchor_m183_row16_loss: 0.0000096218
```

Interpretation:

```text
M297/M270 scalar exact losses did not regress.
The combined active-set/action-distance exact contract did regress.
The raw PPO proposal moved outside the accepted proof trust region even before
closed-loop replay gates were checked.
```

This means the next step should not be a fresh PPO repeat. The PPO update needs
an exact post-step projection or a stronger proof-preserving trust region.

## Old Public Replay Localization

Old public replay gates:

```text
m183_m168: 14 / 16 success drops retained, failed
m183_m170: 16 / 17 success drops retained, failed
m193_m189: 14 / 14 success drops retained, passed
m212_m204: 17 / 17 success drops retained, passed
m223_m219: 17 / 17 success drops retained, passed
m267_m264: 16 / 17 success drops retained, failed
```

Failed rows:

```text
m183_m168:
  row 9  physical_pair 9530:21:9540:24  wrong_margin +0.000154
  row 10 physical_pair 9530:24:9540:27  wrong_margin +0.001163

m183_m170:
  row 10 physical_pair 9530:24:9540:27  wrong_margin +0.000701

m267_m264:
  row 15 physical_pair 9530:21:9550:21  wrong_margin +0.000660
```

All failed rows preserve normal-history success. The failure mechanism is
specific: wrong-history branches became safe with small positive margins.

## Family-Intersection Localization

M1061 family-intersection replay gates:

```text
short61049 -> candidate: 21 / 25 success drops retained, failed
short61050 -> candidate: 21 / 27 success drops retained, failed
short61051 -> candidate: 21 / 27 success drops retained, failed
```

Failed row groups:

```text
short61049:
  rows 16,22,23,24
  wrong margins +0.000371 to +0.001075

short61050:
  rows 16,17,23,24,25,26
  wrong margins +0.000029 to +0.000789

short61051:
  rows 16,17,23,24,25,26
  wrong margins +0.000050 to +0.000788
```

This is the most important new evidence from M1069. The failure is not only on
old M183/M267 surfaces. It also appears on the refreshed current-family
intersection corpus, across all three short-PPO family sources.

## Source-Diverse Localization

Source-diverse protected gates:

```text
current_m333_surface: 17 / 17 success drops retained, passed
m317_continuity_surface: 16 / 17 success drops retained, failed
m314_continuity_surface: 16 / 17 success drops retained, failed
```

Both failed continuity surfaces lose row 15:

```text
physical_pair: 9530:21:9550:21
normal_success: true
normal_margin: about +0.00823
wrong_history_success: true
wrong_history_margin: about +0.00017
```

This overlaps the old M267/M264 row-15 failure family.

## Broad Gates

Fresh/OOD gates passed:

```text
fresh_public seed 103900: success delta 0.0, margin delta +0.000860
fresh_public seed 103901: success delta 0.0, margin delta +0.000863
moderate_ood seed 103920: success delta 0.0, margin delta +0.000473
```

Behavior gates passed. Therefore M1069 would look acceptable under aggregate
closed-loop metrics. The expanded proof gates are doing useful work: they catch
a causal self-ID evidence regression that broad success metrics miss.

## Diagnosis

M1069 is a coupled proof washout:

```text
1. exact active-set trust region is violated;
2. old public replay surfaces lose wrong-history failures;
3. current-family M1061 intersection rows lose wrong-history failures;
4. source-diverse continuity rows lose the same row-15 family;
5. broad fresh/OOD and behavior metrics remain stable.
```

The raw PPO direction appears to increase normal margins slightly while also
making wrong-history branches safer. That is exactly the undesired direction for
self-identification evidence: the policy becomes more robust in a way that
erases the counterfactual dependence on correct command-response history.

## What This Rules Out

Do not do these next:

```text
do not promote M1069;
do not repeat the same 8192-step PPO recipe on a new seed;
do not increase PPO length to 16k;
do not weaken the M1061 family-intersection gate;
do not accept fresh/OOD or behavior retention as sufficient.
```

## Recommended Next Step

Route to a design milestone for post-PPO proof projection:

```text
m1071-v4-public-base-medium-ppo-repair-projection-design
```

The design should treat PPO as a proposal generator, not as an automatically
accepted update:

```text
base: M1049 public-gate base
proposal: M1069 raw checkpoint

first-order acceptance:
  exact M997/M297/M270 and combined active-set no-regression

second-order acceptance:
  old public replay gates
  M1061 family-intersection gates
  source-diverse continuity gates
  fresh/OOD and behavior gates

repair/projection ingredients:
  line search from base to raw;
  exact full-corpus active-set objective;
  failed old replay rows 9/10/15;
  failed M1061 family-intersection rows 16/17/22/23/24/25/26;
  failed source-diverse continuity row 15;
  trust region to M1049 base;
  no actor-input changes;
  no private holdout.
```

The next experiment should be design/projection-first, not another PPO run.

## Decision

```text
medium_ppo_proof_washout_audit_route_to_repair_projection_design
```
