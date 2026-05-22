# M212 Current-Family Boundary Objective Sanity

M212 converts the M211 robustness-passing current-family boundary surface into
replay-aligned objective corpora before any actor update or PPO.

No PPO, actor update, or actor input change is run in this milestone.

## Source Rows

Input:

```text
runs/m211_current_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
```

The M211 surface contains `171` accepted wrong-history rows across `13`
physical pairs, `8` left steps, `3` checkpoints, `2` targets, and `2` normal
margin buckets.

## Objective Corpora

All corpora use:

```text
max_rows_per_physical_pair = 2
optimization_seeds = 10040,10041,10042
steps = 180
hidden_dim = 96
```

| Source checkpoint | Rows | Physical pairs | Targets | Objective pass | Min val combined improvement | Min val delta improvement | Min val pairwise acc |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| m204_5209 | 17 | 13 | 2 | true | 2.940994 | 3.602623 | 1.000000 |
| m202_5206 | 16 | 13 | 2 | true | 2.922968 | 3.575542 | 1.000000 |
| m199_5201 | 15 | 12 | 2 | true | 2.828185 | 3.497041 | 1.000000 |

Artifacts:

- `runs/m212_m204_boundary_outcome_corpus_seed10040`
- `runs/m212_m202_boundary_outcome_corpus_seed10040`
- `runs/m212_m199_boundary_outcome_corpus_seed10040`

The current-best M204 corpus is the primary one for the next actor-update
design.

## Replay Sanity

Artifacts:

- `runs/m212_m204_boundary_replay_sanity_seed10040`
- `runs/m212_m202_boundary_replay_sanity_seed10040`
- `runs/m212_m199_boundary_replay_sanity_seed10040`

| Corpus | Baseline | Candidate | Rows | Baseline drops | Candidate drops | Normal success delta | Gate pass |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| m204_5209 | m204_5209 | m202_5206 | 17 | 17 | 17 | 0.0 | true |
| m202_5206 | m202_5206 | m199_5201 | 16 | 16 | 16 | 0.0 | true |
| m199_5201 | m199_5201 | m202_5206 | 15 | 15 | 13 | 0.0 | false |

The M199 corpus is a mixed family comparison only. Its cross-family replay
failure shows that the oldest stage2 rows are less stable when replayed through
the later M202 checkpoint. It does not block the current-best M204 path.

The M204 current-best corpus passes replay sanity:

- normal success remains `1.0`;
- wrong-history success remains `0.0`;
- success drops remain `17/17`;
- normal margin delta is `-0.000308`, inside the `0.005` regression limit;
- margin-gap delta is `-0.000168`, inside the `0.001` regression limit.

## Decision

M212 is positive for the current-best M204 path.

What it proves:

- M211 accepted rows can be converted into compact, source-diverse objective
  corpora;
- the M204 corpus is learnable across three objective seeds;
- the M204 corpus replays as normal-history success and wrong-history failure;
- adjacent M202 replay preserves the M204 success-drop rows.

What it does not prove:

- that an actor update will preserve behavior and old/new replay gates;
- that M199's older rows are robust across later checkpoints;
- that PPO can resume.

Decision:

```text
admit_guarded_actor_update_design
```

Next step:

```text
m213-m212-guarded-actor-update
```

M213 may run only a tiny anchored actor update from M204 using the M212 M204
boundary-outcome corpus. It must preserve behavior, the old M183 replay
surfaces, the old M193 replay surface, the new M212 M204 replay surface, and the
protected key before any PPO is reconsidered.
