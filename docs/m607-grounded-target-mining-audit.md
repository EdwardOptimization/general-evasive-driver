# M607 Grounded Target Mining Audit

## Purpose

M607 audits the M606 zero-accepted grounded target-mining result before changing
search, thresholds, or optimizer scope.

Question:

```text
Why did the M606 local first-action search produce zero accepted targets?
```

Scope:

```text
no training
no PPO
no checkpoint promotion
no threshold retrofitting
no conversion of M604 belief-only gaps into labels
```

## Source

M607 uses:

```text
runs/m606_grounded_capability_action_target_miner/summary.json
runs/m606_grounded_capability_action_target_miner/selected_source_rows.csv
runs/m606_grounded_capability_action_target_miner/target_candidates.csv
runs/m606_grounded_capability_action_target_miner/unaccepted_rows.csv
```

M606 selected `23` unique source rows and evaluated `4508` local first-action
candidate rollouts.

## M606 Result

| Metric | Value |
| --- | ---: |
| selected source rows | `23` |
| candidate rollouts | `4508` |
| trust-region candidate rollouts | `3696` |
| accepted targets | `0` |
| unaccepted rows | `23` |
| max candidate margin improvement | `0.014268` |
| max trust-region margin improvement | `0.013046` |
| max candidate risk improvement | `0.014268` |
| max trust-region risk improvement | `0.013046` |

Rejection counts:

| Reason | Count |
| --- | ---: |
| insufficient margin or risk improvement | `3214` |
| outside action trust region | `812` |
| candidate collision | `482` |

## Boundary Distance Audit

Baseline source margins are mostly not near the short-horizon safety boundary:

| Metric | Value |
| --- | ---: |
| mean baseline margin | `2.833607` |
| median baseline margin | `2.729036` |
| min baseline margin | `-0.191270` |
| max baseline margin | `7.419653` |
| baseline margin `< 0` | `3 / 23` |
| baseline margin `<= 0.1` | `3 / 23` |
| baseline margin `<= 0.5` | `4 / 23` |

This is the main explanation. Most selected M604 belief-only rows are readable
capability/action-coupling gaps, but they are not local first-action recovery
states where a small action change can create a meaningful simulator margin
delta over `40` continuation steps.

## Threshold Audit

M607 does not lower thresholds or reinterpret M606 as accepted. The what-if
counts below are diagnostic only:

| Diagnostic threshold | Candidate count | Source rows |
| --- | ---: | ---: |
| margin `>= 0.005` or risk `>= 0.010` | `173` | `9` |
| margin `>= 0.010` or risk `>= 0.010` | `20` | `3` |
| margin `>= 0.015` or risk `>= 0.010` | `0` | `0` |
| margin `>= 0.020` or risk `>= 0.010` | `0` | `0` |

Even an easier `0.015` margin threshold would still accept no candidates. The
pre-registered `0.02` margin threshold is not the only blocker.

## Search Locality Audit

The best candidate for most rows is at the same local grid corner:

```text
steer_delta    +0.08
throttle_delta -0.06
brake_delta    +0.08
action_l2      0.128062
```

That is outside the configured `0.10` trust region. More importantly, even this
larger move improves the best margin by only `0.014268`. Inside the trust
region, the best improvement is `0.013046`.

This says widening the grid alone is not the right immediate next step. It may
increase action drift or collisions without producing grounded target quality.

## Classification

The M606 zero-accepted result is classified as:

```text
primary: source-row boundary-distance issue
secondary: first-action locality and weak short-horizon utility signal
not primary: acceptance threshold artifact
not primary: missing implementation artifact
```

M606 wrote all required artifacts and changed no actor weights.

## Decision

Decision:

```text
grounded_target_mining_audit_admit_boundary_conditioned_source_design
```

Do not train from M604 belief-only gaps. Do not lower thresholds and call M606
accepted.

Next branch:

```text
M608 boundary/risk-conditioned grounded source re-mining design
```

M608 should design source selection that first identifies rows near a
behaviorally meaningful boundary before running local action target search.
The source screen should include at least:

```text
baseline margin window
baseline collision / near-collision status
short-horizon risk sensitivity
source diversity across surface / variant / target / physical pair
normal branch and variant branch preservation requirements
```

Only after that source screen should a new grounded target miner run. Actor
training, PPO, and checkpoint promotion remain blocked.

## Contract Checks

```text
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
private_holdout_used: false
```
