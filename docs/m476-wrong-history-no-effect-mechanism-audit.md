# M476 Wrong-History No-Effect Mechanism Audit

## Purpose

M476 audits why the source-diverse M475 wrong-history interventions remain
closed-loop no-effect rows. The goal is to classify the mechanism before
designing another proof path.

No training, PPO, actor-input change, proof expansion, or checkpoint promotion
is performed.

## Inputs

```text
runs/m475_combined_adversarial_action_gate/action_interventions.csv
runs/m475_combined_adversarial_outcome_gate/outcome_interventions.csv
runs/m475_combined_adversarial_outcome_selector/candidates.csv
runs/m475_combined_adversarial_near_boundary_selector/wrong_history_classified.csv
```

Audit artifacts:

```text
runs/m476_wrong_history_no_effect_mechanism_audit/summary.json
runs/m476_wrong_history_no_effect_mechanism_audit/variant_mechanism_comparison.csv
runs/m476_wrong_history_no_effect_mechanism_audit/wrong_history_by_action_distance_bin.csv
runs/m476_wrong_history_no_effect_mechanism_audit/wrong_history_by_normal_margin_bin.csv
runs/m476_wrong_history_no_effect_mechanism_audit/wrong_history_by_target.csv
runs/m476_wrong_history_no_effect_mechanism_audit/wrong_history_by_label.csv
```

## Main Finding

Wrong matched history is not completely ignored, but its closed-loop effect is
much smaller than reset or zero-current interventions:

```text
variant                 action_mean  traj_mean  success_drop  outcome_critical  accepted
wrong_matched_history     0.053586   0.045794             0                 0         0
reset_hidden              0.620908   0.883482            10                46         5
zero_current_response     0.122251   0.395153            10                36        23
zero_action_history       0.030448   0.116173             1                 3         0
delayed_history           0.019510   0.006594             0                 0         0
```

This means the task surface can show outcome degradation, but wrong matched
history does not create enough persistent trajectory deviation.

## Wrong-History Details

```text
wrong-history rows:                     197
action-prefilter pass rows:             131
closer-to-right-action rows:            124
action distance mean:              0.053586
action distance max:               0.151947
trajectory distance mean:          0.045794
trajectory distance max:           0.287908
success-drop rows:                        0
collision-gap rows:                       0
completion-drop rows:                    0
outcome-critical rows:                   0
accepted rows:                           0
margin gap mean:                 -0.000467
margin gap max:                   0.010044
```

The margin proof threshold is `0.02`; only one row reaches even `0.01`.

## Action-Distance Bins

Even the strongest wrong-history action changes do not produce terminal-margin
degradation:

```text
bin          count  action_pass  closer_right  success_drop  margin_gap_max
<=0.025         67            6             6             0        0.000421
0.025-0.05      19           15            15             0        0.010044
0.05-0.075      32           31            29             0        0.003845
0.075-0.10      57           57            56             0        0.003872
>0.10           22           22            18             0        0.004904
```

This argues against a simple "raise min action distance" fix. Rows with
`action_distance > 0.10` still have max margin gap only `0.004904`.

## Normal-Margin Bins

The no-effect result is not just high terminal slack:

```text
normal margin bin  count  action_pass  success_drop  margin_gap_max
<=0.05                 4            0             0        0.000000
0.05-0.10             43           33             0        0.000773
0.10-0.25             20            6             0        0.002564
0.25-0.50             62           48             0        0.004904
0.50-0.75             68           44             0        0.010044
```

There are `47` rows under `0.10 m` normal margin, but wrong history still
does not produce success, collision, completion, or proof-margin degradation.

## Interpretation

The dominant mechanism is:

```text
wrong_history_action_and_trajectory_perturbations_are_too_weak_or_too_quickly_corrected_relative_to_reset_zero_current
```

M474 solved the source-diverse pair availability problem. M475/M476 show the
next problem: a one-shot wrong matched-history hidden injection changes some
first actions, but the policy appears to recover through current observations
before terminal outcome changes.

Therefore the next proof path should not be more source-pool expansion or
threshold tuning. It should test whether wrong belief must persist later into
the emergency phase to become outcome-critical.

## Decision

```text
wrong_history_no_effect_audit_admit_m477_persistent_intervention_design
```

M477 should design a persistent or later wrong-history intervention probe. The
probe should stay diagnostic: no training, no actor-input change, and no
checkpoint promotion.
