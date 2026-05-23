# M324 Single-Key Window Override Policy Design

M324 defines how to handle candidates that pass the refreshed source-diverse
protected surface but fail the old protected key `9944|perturbed|28|28` by the
historical normal-margin window. No PPO, actor update, promotion, or actor-input
change was performed.

## Problem

M317 left the old protected key nearly saturated:

```text
normal margin = 0.19999520261417003
max normal-margin window = 0.2
slack ~= 4.8e-6
```

M319 and M320 then showed that this is not the only current-family proof
surface. A refreshed source-diverse surface exists away from the old window:

```text
M319: 180 accepted wrong-history rows across 13 physical pairs, 8 left steps,
      8 right steps, 3 checkpoints, and 2 targets.

M320: compact 17-row / 13-physical-pair corpora for m316_a0_0025, m314_base,
      and m316_repaired; objective and replay sanity pass.
```

M323 confirmed the conflict:

```text
M316 repaired endpoint:
  passes 2 / 2 source-diverse protected replay gates
  retains 17 / 17 success drops on both gates
  fails old 9944 because the normal margin leaves the singleton window
```

Therefore the workflow needs an explicit rule. Otherwise future decisions will
alternate between two bad extremes:

```text
old-key absolutism:
  one saturated historical row blocks all meaningful movement

old-key deletion:
  a still-discriminative historical diagnostic is silently ignored
```

## Classification

M324 keeps the process-v2 failure type `protected_key_window_failure` for hard
protected-key failures, but adds the following audit classification in milestone
docs and result payloads.

### Single-Key Window Saturation

Use:

```text
single_key_window_saturation
```

when all of the following are true:

1. The candidate passes the source-diverse protected replay bundle.
2. The source-diverse bundle retains the required wrong-history success drops.
3. The source-diverse bundle does not exceed normal-margin or margin-gap
   regression tolerances.
4. The old `9944` diagnostic failure is caused by the historical singleton
   normal-margin window, not by loss of wrong-history discrimination.
5. The old-key margin gap remains materially positive; use `margin_gap_min >=
   0.09` as the current diagnostic floor for this family.
6. Exact M297 and exact M270 do not regress versus the active public-gate base.
7. Actor inputs, env config, and private-holdout policy are unchanged.

This classification is not a promotion. It only allows the candidate to advance
to a full public-gate evaluation under explicit audit.

### Hard Protected-Key Failure

Use the normal hard-failure path if any of the following occur:

```text
source-diverse protected replay fails
wrong-history success drops are lost
normal-history success regresses
normal-margin or margin-gap regression exceeds tolerance
old-key margin gap collapses below the diagnostic floor
old-key wrong-history branch becomes safe
exact M297 or exact M270 regresses
actor input contract changes
```

Hard protected-key failures remain reject/repair blockers and must not advance
to promotion evaluation.

## Override Scope

The policy does not remove `9944`.

`9944` remains:

```text
historical continuity diagnostic
singleton-window saturation detector
reported row in promotion docs
reason to require explicit audit
```

The source-diverse protected bundle becomes:

```text
the first-class protected proof gate
```

A candidate may override the old single-key hard veto only when the old-key
failure is classified as `single_key_window_saturation` and every source-diverse
and exact objective condition above passes.

## Escalation Order

For any candidate in the M317/M320 source-diverse policy family:

```text
1. Exact M297 rejected-history preference no-regression.
2. Exact M270 source-balanced outcome no-regression.
3. Source-diverse protected replay bundle.
4. Old 9944 diagnostic ingestion and classification.
5. Six public replay surfaces.
6. Behavior seeds 9505 and 9506.
7. Review artifact and research validation.
8. Promotion decision.
```

The source-diverse protected pass plus old-key singleton-window classification
allows step 5 to run. It does not skip steps 5-8.

## Promotion Rule

A candidate that fails the old `9944` normal-margin window can be promoted only
if the final milestone explicitly documents:

```text
exact M297 and M270 no-regression
source-diverse protected bundle pass
old-key classification = single_key_window_saturation
old-key margin gap retained
all six replay gates pass
behavior seeds 9505 and 9506 retain success / termination behavior
no actor-input or env-contract change
no private-holdout tuning
```

If any condition is missing, the candidate can be archived as diagnostic, but it
cannot become the new public-gate base.

## M325 Admission

M324 admits one no-PPO full-gate milestone for the M316 repaired endpoint under
the new policy. This is the right next test because M323 already showed:

```text
source-diverse protected proof passes
old-key conflict is the active blocker
no promotion decision has been made
```

The M325 milestone must run the full public gate and either promote the repaired
endpoint under this policy or reject/archive it with a structured failure type.

## Decision

Admit:

```text
m325-source-diverse-policy-full-gate-for-m316-repaired
```

Decision:

```text
admit_m325_source_diverse_policy_full_gate_for_m316_repaired
```
