# M1387 Paper-Route History-Profile One-Seed Smoke Result Audit

## Purpose

M1387 audits M1386 before deciding whether to scale the fixed-budget
history-profile refresh to a 3-seed public pilot.

M1387 does not train, run PPO, run new evaluation, promote, use private holdout,
export a corpus, change actor inputs, or claim profile ranking.

## M1386 Evidence

Artifact:

```text
runs/m1386_history_profile_fixed_budget_smoke/summary.json
```

Completion:

```text
result_class: corrected_profile_pilot_completed
profile_count: 8
total_seed_runs: 8
completed_seed_runs: 8
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
actor_input_contract_changed: false
```

M1386 therefore passes as a one-seed training/evaluation plumbing smoke.

## One-Seed Signal Audit

Success / collision / mean margin:

| Profile | Success | Collision | Mean Margin |
| --- | ---: | ---: | ---: |
| `L0_current_masked` | 0.62500 | 0.37500 | 1.34657 |
| `L1_one_step` | 0.50000 | 0.50000 | 0.97907 |
| `L2_window_13` | 0.21875 | 0.31250 | 1.39730 |
| `L2_window_13_current_tiled` | 0.21875 | 0.31250 | 1.38395 |
| `L2_window_25` | 0.21875 | 0.31250 | 1.39973 |
| `L2_window_25_current_tiled` | 0.21875 | 0.31250 | 1.38527 |
| `L3_online_gru` | 0.62500 | 0.37500 | 1.19125 |
| `L3_reset_control_corrected` | 0.62500 | 0.37500 | 1.22975 |

Classification:

```text
plumbing_pass: true
architecture_ranking_evidence: false
finite_window_history_necessity: not_supported_in_one_seed
online_gru_hidden_advantage: not_supported_in_one_seed
current_frame_substitution_risk: high
```

Reasons:

```text
L2 normal and current-tiled controls tie on success and collision.
L3 online and corrected reset-control tie on success and collision.
L0 current-only is tied with L3 success in this seed block.
One training seed cannot estimate seed stability.
```

This does not mean L3 is useless. It means M1386 is not evidence of recurrent
hidden benefit, and the next step must keep the claim scope narrow.

## Decision

Decision:

```text
history_profile_one_seed_audit_admit_three_seed_public_pilot
```

Rationale:

```text
M1386 verifies that all eight profiles train and evaluate cleanly.
The runtime cost is low enough that a 3-seed public pilot is a reasonable next
stability check.
The one-seed parity signals make a 3-seed pilot useful only as public trend
evidence, not as a ranking or self-ID claim.
```

Next:

```text
m1388-paper-route-history-profile-three-seed-public-pilot
```

M1388 must be the last profile-scaling step before another audit. If M1388 again
shows L2/current-tiled parity and L3/reset parity, the branch should route to a
stronger causal history-necessity diagnostic or task redesign rather than
another blind profile repeat.

## Guardrails

M1387 performs no training, PPO, new evaluation, actor update, checkpoint
mutation, promotion, private holdout, threshold relaxation, actor-input
expansion, corpus export, high-fidelity claim, paper-level profile-ranking
claim, recurrent-belief advantage claim, or level3 self-identification claim.
