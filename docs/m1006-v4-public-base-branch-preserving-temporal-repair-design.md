# M1006 V4 Public Base Branch-Preserving Temporal Repair Design

## Purpose

M1006 designs the next repair route after M1004/M1005 showed that the plain
temporal sequence objective creates exact candidates but washes out M267/M264
wrong-history proof rows.

This milestone is design-only. It does not train, run PPO, run replay gates,
use private holdout, change actor inputs, or promote.

## Diagnosis To Preserve

M1004/M1005 established:

```text
exact_contract_pass_count: 5 / 5
M267/M264 preflight pass count: 0 / 5
smallest alpha: 0.01
smallest-alpha lost rows: 6, 15
failure type: proof_washout
subtype: wrong_history_branch_lift
```

The failure is not normal-history regression. The exact temporal update makes
the correct branch slightly safer, but also makes near-boundary wrong-history
rollouts cross from failure to success.

## Design Principle

The next objective must keep three things separated:

```text
positive behavior target:
  M997 normal temporal sequences under correct history

contrast-only temporal histories:
  reset_then_warm_history / delayed_capability_history hidden states from M997

public proof branch retention:
  M267/M264 wrong-history rows, especially rows 6 and 15
```

The repair must not train the actor to imitate degraded wrong-history actions
as a positive driving behavior. Wrong-history branches are proof-retention
constraints, not deployable behavior targets.

## Trainable Surface

The first repair should remain conservative:

```text
trainable:
  actor_mean.weight
  actor_mean.bias

frozen:
  response_encoder.*
  context_encoder.*
  response_context_fusion.*
  online_gru_cell.*
  critic.*
  log_std
```

If this surface cannot produce a candidate with both temporal exact improvement
and M267/M264 preflight retention, the branch should synthesize before opening a
wider surface.

## M1007 Implementation Scope

M1007 should implement a no-update exact evaluator and corpus bridge first, not
an actor update.

Required inputs:

```text
M997 temporal sequence corpus:
  runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz

M1000 base temporal summary:
  runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json

M267/M264 public proof surface:
  runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv

M1004 row-level replay diagnostics:
  runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/*/boundary_replay_rows.csv
```

The evaluator should reconstruct a compact active proof set:

```text
primary active rows:
  6, 15

secondary active rows:
  11, 16

full preflight set:
  all 17 M267/M264 rows
```

Rows `6` and `15` are mandatory because they fail even at alpha `0.01`. Rows
`11` and `16` are secondary because they fail at alpha `0.05`. The full 17-row
closed-loop preflight remains the final arbiter.

## Objective Terms

### 1. Temporal Positive Term

Keep the M999/M1002 temporal sequence loss:

```text
L_normal_sequence =
  weighted NLL of M997 normal rollout actions
  under normal/correct initial hidden state
```

This remains the only direct behavior-imitation target.

### 2. Temporal Hidden Preference Term

Keep the temporal contrast:

```text
L_temporal_preference =
  softplus((logp_variant_on_normal - logp_normal) / sequence_length + margin)
```

This says the normal sequence should be more likely under correct history than
under disrupted temporal history. It does not train toward variant/degraded
actions.

### 3. Base Logp Anchor

Keep the base-logp anchor:

```text
L_base_logp_anchor =
  square((logp_normal_candidate - logp_normal_base) / sequence_length)
```

This limits drift on M997 normal sequences.

### 4. Public Proof Branch Ceiling

Add a new branch-preserving proof term on the M267/M264 active rows:

```text
L_branch_ceiling =
  weighted relu(logp_wrong_candidate_on_normal_safe_sequence
                - logp_wrong_base_on_normal_safe_sequence
                - epsilon_logp)^2
```

Interpretation:

```text
Under wrong-history hidden state, do not make the normal safe sequence more
likely than it was at the M974 public base.
```

This is a ceiling, not imitation of wrong-history degraded behavior.

### 5. Wrong-vs-Normal First-Action Separation Floor

Add a second proxy term:

```text
L_branch_separation =
  weighted relu(d_min
                - ||a_normal_candidate(h_normal)
                    - a_normal_candidate(h_wrong)||_2)^2
```

This prevents the wrong-history branch from collapsing to the same first action
as the normal branch on active public proof rows. It still does not target the
old wrong-history action.

Initial values:

```text
epsilon_logp: 0.005 per step
d_min: max(0.02, 0.75 * base_first_action_distance)
active row weights:
  row 6: 4.0
  row 15: 4.0
  row 11: 2.0
  row 16: 2.0
  other M267/M264 rows: 1.0
```

### 6. Combined Repair Loss

Recommended first combined loss:

```text
L =
  L_normal_sequence
+ lambda_pref * L_temporal_preference
+ lambda_anchor * L_base_logp_anchor
+ lambda_branch_ceiling * L_branch_ceiling
+ lambda_branch_separation * L_branch_separation
```

Initial coefficients:

```text
lambda_pref: 1.0
lambda_anchor: 0.25
lambda_branch_ceiling: 10.0
lambda_branch_separation: 2.0
```

M1007 should only evaluate these terms at the M974 base and on M1002
candidates. M1008 can run a small actor_mean-only update only if M1007 proves
the objective is finite, active on rows `6/15`, and separates good M974-like
states from M1002 proof-washing states.

## Exact Gates Before Actor Update

M1007 no-update evaluator should report:

```text
finite metrics
M997 temporal base metrics reproduce M1000
branch ceiling loss near zero for M974 base
branch ceiling loss positive for M1002 alpha 0.01 and larger alphas
branch separation loss positive for M1002 proof-washing alphas
active row table for rows 6, 15, 11, 16
no actor parameter changes
```

M1008 actor update can be admitted only if M1007 passes those sanity checks.

## Candidate Gates For The Future Update

The future M1008 update must keep the M1002 exact temporal gates and add
branch-retention gates:

```text
weighted_total_loss <= M1000 base - 0.001
weighted_normal_sequence_nll <= M1000 base + 0.005
weighted_temporal_preference_loss <= M1000 base + 0.005
weighted_logp_gap_mean >= M1000 base - 0.050
temporal_logp_gap_p10 >= M1000 base - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080

branch_ceiling_loss <= base + 1e-6
branch_separation_floor_pass for rows 6 and 15
only actor_mean changes
```

After exact gates:

```text
1. M267/M264 full preflight, not just rows 6 and 15;
2. six public replay surfaces only if M267/M264 passes;
3. behavior seeds only if public replay passes;
4. no PPO or promotion.
```

## Stop Rules

Stop the branch and synthesize if:

```text
M1007 cannot produce a clean branch-ceiling evaluator;
M1008 finds no alpha that passes both temporal exact and M267/M264 preflight;
branch-retention terms require training toward old wrong-history actions;
actor_mean-only remains insufficient and the branch has reached cadence.
```

## Decision

```text
branch_preserving_temporal_repair_design_admit_m1007_evaluator
```

Next:

```text
m1007-v4-public-base-branch-preserving-temporal-repair-evaluator
```
