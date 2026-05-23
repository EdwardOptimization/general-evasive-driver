# M445 Fresh Policy-Difference Miner Design

M445 designs the next generalization tool after M444 found no broad aggregate
success differences between the current base and recent proof/utility
candidates. No training, PPO, benchmark run, checkpoint promotion, or actor
input/output change is part of this milestone.

## Motivation

M444 showed that a 160-episode fresh benchmark is too coarse for the current
branch:

```text
M399 base success = 0.8625
all checkpoint candidate success deltas = 0.0
all per-seed success-difference counts = 0
```

M427 retains more of the M406 old-key recovery direction than proof-safe
active-boundary candidates, but it does not improve broad success, collision
rate, or return in the M444 distribution. That means M406 recovery retained
should not be treated as a broad driver-performance proxy.

The next surface should therefore be mined from fresh policy differences:

```text
Find scenarios where policies actually diverge in closed-loop outcome,
terminal margin, return, or near-boundary behavior.
```

Only after such scenarios exist should the project design another objective or
PPO repair.

## Policy Set

The first miner should compare:

| Role | Policy |
| --- | --- |
| base | `m399_base` |
| proof-safe radius | `m434_r0010` |
| proof-safe active-boundary | `m438_r0015` |
| high-utility proof-rejected | `m427_high_utility` |
| latest rejected v2 | `m442_tail_v2` |

The miner should also allow more policies later, but M446 should keep this
initial set fixed for reproducibility.

## Fresh Scenario Pool

M446 should implement the miner and smoke it on existing M444 rows. The first
full run after that should use a fresh pool, not M444:

```text
env config: configs/m121_human_view_zero_obstacle_relvel.json
seed block: 9700-10723
episodes: 1024
device: cpu
```

If runtime is too high, the first full run can use `512` episodes with the same
schema, then escalate to `1024`.

M444 remains public diagnostic evidence. Do not reuse it as a private holdout.

## Divergence Types

The miner should emit one candidate row per `(seed, candidate_policy)` when any
of these conditions is true versus `m399_base`:

| Type | Acceptance rule | Purpose |
| --- | --- | --- |
| `success_flip` | candidate success differs from base success | strongest closed-loop behavioral difference |
| `collision_flip` | candidate collision differs from base collision | safety-specific outcome difference |
| `margin_sign_flip` | `min_clearance_margin` changes sign | near-boundary safety sign change |
| `near_boundary_margin_delta` | `abs(delta_margin) >= 0.01` and either margin is within `0.25` of zero | find boundary motion that broad success hides |
| `large_margin_delta` | `abs(delta_margin) >= 0.05` | find larger non-terminal trajectory differences |
| `return_delta` | `abs(delta_return) >= 1.0` | catch reward-level behavior changes |

The first implementation should make thresholds CLI parameters with these
defaults.

## Scoring

Use a transparent score so accepted rows can be sorted before diversity
selection:

```text
score =
  100.0 * success_flip
+  80.0  * collision_flip
+  60.0  * margin_sign_flip
+  20.0  * min(abs(delta_margin) / 0.05, 5.0)
+  5.0   * min(abs(delta_return) / 5.0, 5.0)
+  2.0   * near_boundary_flag
```

Do not use hidden physical parameters as actor inputs. Hidden/environment fields
such as `mu`, `mass_scale`, `brake_scale`, `steer_tau_scale`, and
`obstacle_label` are allowed only for mining, diversity accounting, and docs.

## Diversity Selection

The miner should export both all accepted candidates and a compact selected
corpus.

Compact selection defaults:

```text
max rows: 64
max rows per seed: 1
max rows per candidate policy: 20
max rows per obstacle_label: 24
max rows per mu_bucket: 24
min candidate policies represented if available: 3
min obstacle labels represented if available: 2
min mu buckets represented if available: 2
```

Selection should be greedy by score with these caps. If no accepted rows meet
the thresholds, the miner should still write an empty corpus and a summary that
explicitly says the policy family is indistinguishable under the tested pool
and thresholds.

## Output Artifacts

M446 implementation should produce:

```text
runs/m446_policy_difference_miner_smoke/policy_difference_candidates.csv
runs/m446_policy_difference_miner_smoke/compact_policy_difference_corpus.csv
runs/m446_policy_difference_miner_smoke/policy_difference_summary.json
```

For full fresh runs, use:

```text
runs/m447_fresh_policy_difference_mining_seed9700/
```

Required CSV columns:

```text
seed
candidate_policy
divergence_types
score
base_success
candidate_success
base_collision
candidate_collision
base_margin
candidate_margin
delta_margin
base_return
candidate_return
delta_return
obstacle_label
mu
mu_bucket
mass_scale
brake_scale
steer_tau_scale
source_run
```

The summary JSON should include:

```text
rows_total
accepted_rows
selected_rows
accepted_by_policy
accepted_by_divergence_type
selected_by_policy
selected_by_obstacle_label
selected_by_mu_bucket
max_policy_dominance
max_obstacle_label_dominance
```

## Decision Logic

The miner is evidence infrastructure, not a training objective.

If the full fresh run finds source-diverse success flips or margin-sign flips,
the next branch should build a generalization replay/proof gate from those
scenarios.

If it finds only tiny margin deltas and zero outcome differences, the current
candidate family is functionally indistinguishable on this simulator
distribution. In that case, do not keep tuning old-key recovery. Move instead
to a richer scenario distribution or a new training signal.

## Decision

M445 passes as a design milestone and admits:

```text
m446-policy-difference-miner-implementation
```

M446 should implement the CSV/JSON miner and run a smoke on the existing M444
benchmark output. It should not train or promote any checkpoint.
