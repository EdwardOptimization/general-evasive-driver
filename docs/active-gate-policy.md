# Active Gate Policy

This policy is derived from the M1185 gate utility matrix. It defines how the
project should schedule daily engineering gates, active public proof gates,
extended historical regression, legacy diagnostics, and deprecated objectives
for the paper route.

This document does not delete any historical tools. It does not run replay,
train, run PPO, use private holdout, promote, or change actor inputs.

## Policy Summary

The active policy is:

```text
Stack A: daily engineering and controller-comparison admission.
Stack B: default active public proof gate for public-base and paper-route work.
Stack C: extended regression for promotion, synthesis, paper freeze, and
         difficult failure localization.
Legacy: diagnostic-only unless reinstated by manifest.
Deprecated: not allowed as training or promotion objective without a new
            reinstatement manifest.
```

## Non-Negotiable Contract

Every stack must preserve the deployable actor contract:

- no hidden dynamics parameters in actor input;
- no oracle feasibility labels;
- no reference trajectory, TTC, required clearance, or stopping-distance answer;
- no slip, tire force, friction margin, or other non-deployable tire oracle;
- no private-holdout tuning;
- no actor-input change without an explicit contract-change manifest.

Training-time teachers, corpus miners, and diagnostics may use privileged
values only if the manifest states that they do not enter the deployed actor.

## Stack A: Daily Engineering

Use Stack A for:

- documentation and harness changes;
- controller-family design;
- source-rich metadata tooling;
- initial L0/L1/L2/L3 design and smoke planning;
- broad engineering behavior checks before any performance claim.

Required checks:

- research harness validation;
- actor-contract and no-privileged-input declaration;
- private-holdout isolation;
- basic success/collision/clearance metrics when a driver checkpoint is being
  evaluated;
- fresh/OOD and behavior seeds when already admitted by the manifest.

Allowed claim:

```text
deployable feedback behavior or infrastructure readiness
```

Forbidden claim:

```text
self-identification proof or recurrent-belief advantage
```

Reason: M1069 and M1112 passed broad behavior checks while proof surfaces
washed out. Stack A is necessary but not sufficient.

## Stack B: Active Public Proof

Use Stack B for:

- public-gate base hardening;
- admitting guarded PPO smoke or repair proposals;
- controller comparisons that might support mechanism claims;
- source-rich proof conversion;
- paper-route evidence before private holdout.

Required checks:

- all Stack A checks;
- one compact current proof subset for wrong-history or response-coupling
  retention;
- active terminal-margin row or successor surface if the branch touches a
  known near-boundary mechanism;
- source-diverse surface-quality gate for any newly generated proof surface;
- source-rich metadata sanity for source-rich data generation;
- exact objective checks only for currently active objectives, not every
  historical objective.

Allowed claim:

```text
public proof retention or mechanism-diagnostic readiness
```

Forbidden claim:

```text
paper-level generalization or strong self-identification without L0/L1/L2/L3
comparison and intervention evidence
```

Reason: M1185 shows Stack B catches known wrong-history-safe and
duplicate-dominated surface failures without making every historical row an
unconditional blocker.

## Stack C: Extended Historical Regression

Use Stack C for:

- promotion audits;
- branch synthesis;
- before freezing paper tables;
- after actor architecture, objective, replay, or training-recipe changes;
- when Stack B failure localization is ambiguous;
- when reusing old public-gate base lineage.

Candidate members:

- old public replay surfaces;
- M1061 family-intersection;
- source-diverse protected diagnostics;
- M297/M270 exact preference or successor exact objectives;
- row15/row16 terminal-margin diagnostics;
- legacy protected singleton diagnostics such as old `9944` rows.

Allowed claim:

```text
historical compatibility and extended regression coverage
```

Forbidden claim:

```text
Stack C failure automatically invalidates every engineering baseline
```

Reason: Stack C caught real failures, but it is lineage-specific and partially
redundant with Stack B. It should be run at high-leverage points, not for every
small paper-route design milestone.

## Legacy Diagnostics

Legacy diagnostics remain available for explanation and compatibility audits.
They should not be single-row global blockers unless a new manifest shows
unique coverage against a current known-bad candidate.

Current legacy diagnostic:

```text
old_9944_protected_singleton
```

Policy:

- keep the artifacts and docs;
- do not delete tooling;
- do not use as an unconditional blocker;
- reinstate only through a candidate-based utility audit.

## Deprecated Objectives

Deprecated objectives must not guide future training, repair, or promotion.
They may remain in docs for provenance.

Current deprecated class:

```text
sign_wrong_or_metric_artifact_objectives
```

Policy:

- do not use as a training loss or promotion gate;
- do not delete historical docs;
- require a new reinstatement manifest if any deprecated objective is proposed
  for future use.

## Trigger Table

| Work type | Required stack |
| --- | --- |
| Docs or process-only milestone | Stack A process subset |
| Tooling that does not evaluate a driver | Stack A process subset plus metadata sanity if applicable |
| New driver checkpoint smoke | Stack A |
| Public-base hardening candidate | Stack B |
| Guarded PPO admission | Stack B before PPO and Stack B after proposal |
| Promotion audit | Stack B plus Stack C |
| Paper table freeze | Stack B plus Stack C plus private holdout protocol |
| L0/L1/L2/L3 design milestone | Stack A process subset |
| L0/L1/L2/L3 controlled behavior run | Stack A plus Stack B if mechanism claims are evaluated |
| Mechanism intervention claim | Stack B and source-diverse intervention diagnostics |

## Failure Classification

Use the existing process taxonomy:

- `proof_washout` if Stack A passes but Stack B/C wrong-history or proof gates
  fail;
- `scenario_sampling_failure` if source budget is broad but materialized proof
  rows collapse to duplicate active sets;
- `metric_artifact` if a scalar objective improves while closed-loop proof or
  behavior regresses;
- `contract_violation` if actor input or private-holdout rules are broken;
- `promotion_gate_failure` if Stack B or Stack C blocks a promotion audit.

## Immediate Consequence

The next paper-route work can proceed to L0/L1/L2/L3 controller comparison
design using Stack A process gates. The design must state when Stack B becomes
active:

- when a controller comparison makes a mechanism claim;
- when a candidate checkpoint is proposed for public-base admission;
- when source-rich proof rows are converted;
- before any private-holdout or paper-level result.

The next registered milestone is:

```text
m1187-paper-route-l0-l1-l2-l3-controller-comparison-design
```
