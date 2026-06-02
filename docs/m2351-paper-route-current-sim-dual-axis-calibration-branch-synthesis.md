# M2351 Paper-Route Current-Sim Dual-Axis Calibration Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_candidate_pack_reset_validation_design`
- manifest: `experiments/manifests/m2351-paper-route-current-sim-dual-axis-calibration-branch-synthesis.json`
- synthesis artifact: `docs/m2351-paper-route-current-sim-dual-axis-calibration-branch-synthesis.md`
- synthesis window: `M2346-M2350`
- reset/rollout/policy action in M2351: `false`
- measured execution in M2351: `false`
- training/replay/PPO in M2351: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- reset-valid scenario pack claim made: `false`

## Evidence Summary

M2346-M2350 turned the dual-axis current-sim task-quality blocker into bounded
candidate artifacts:

```text
M2346:
  designed G/H/GH dual-axis calibration route.

M2347:
  materialized 53 candidate rows from 26 redesign rows:
    G candidates 28
    H candidates 13
    GH candidates 12
  preserved secondary coverage rows 9 inactive.

M2348:
  accepted M2347 artifacts and blocked direct validation over raw candidates.

M2349:
  designed a five-pack config materialization route.

M2350:
  materialized five artifact config packs:
    baseline_reference_pack
    g_primary_pack
    h_primary_pack
    g_h_primary_pack
    gh_minimal_pack
```

M2350 output:

```text
candidate_input_count: 53
config_pack_count: 5
modified_config_pack_count: 4
baseline_reference_pack_count: 1
g_primary_selection_count: 13
h_primary_selection_count: 13
g_h_primary_selection_count: 26
gh_minimal_selection_count: 26
env_config_patch_count: 78
metadata_only_patch_count: 37
unresolved_patch_count: 0
active_config_overwritten: false
guardrail_violation_count: 0
```

The branch hit the harness local-search guard after M2350. This synthesis is
therefore required before any further result audit, repair, or reset-validation
design.

## Supported Claims

M2351 supports these bounded claims:

- The 26-row redesign blocker now has a bounded dual-axis candidate artifact
  chain.
- Raw candidate-combination search is no longer the next route; the branch has
  a five-pack candidate family.
- Active config overwrite did not happen.
- No candidate pack has been used for reset, rollout, measured execution,
  controller ranking, or paper evidence.
- The metadata-only patch caveat is explicit and measurable:

```text
metadata_only_patch_count: 37
unresolved_patch_count: 0
```

## Falsified Claims

M2351 blocks or falsifies these claims:

- The current-sim scenario pack is already redesigned.
- The candidate packs are reset-valid.
- Controller-family comparison is ready.
- Support-policy ranking is admissible.
- Finite-window vs GRU can be compared on these packs now.
- The branch provides level3 self-identification evidence.
- Further small artifact/routing steps may continue without synthesis.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  Still the dominant scientific blocker. The branch addresses task-pack quality
  by creating candidate packs, but no reset validation has run.

metric_artifact:
  Prior R0/R4 metric artifacts are bounded. M2350 introduces a new explicit
  metadata-only patch caveat, but unresolved_patch_count is 0, so this is an
  audit item rather than a hard repair blocker.

contract_violation:
  No actor-contract or active-config overwrite violation is observed in M2350.

local_search_guard:
  Triggered correctly. The branch produced several artifact-only design and
  materialization milestones without new closed-loop data, so synthesis is
  required before continuing.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate.

The branch is still operating on public M2343/M2347 artifacts, but the risk is
controlled by two decisions:

```text
1. Raw 53-candidate validation was blocked.
2. Candidate combinations were collapsed into five deterministic packs.
```

The next route should produce new validation evidence rather than another
artifact-only local-search step. However, reset validation should be designed
first because M2350 packs include metadata-only caveats.

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new claim. No driver checkpoint is evaluated.

mechanism evidence for history dependence:
  no new support. No finite-window, GRU, wrong-history, reset-hidden, or
  zero-history comparison is run.

scenario/task-quality evidence:
  positive artifact evidence. The branch creates bounded candidate packs for
  current-sim task-quality redesign.

high-fidelity validation readiness:
  not ready. Current-sim candidate packs are not reset-validated.

workflow or complexity reduction:
  positive. The synthesis stops materialization local search and routes toward
  bounded reset validation design.
```

## Metadata Caveat Interpretation

M2350 reports:

```text
metadata_only_patch_count: 37
unresolved_patch_count: 0
```

This does not block reset-validation design, because all packs are artifact
files and no active config was overwritten. It does block any claim that the
packs are reset-valid or executed. The next reset-validation design must:

```text
1. include all five packs;
2. separately report metadata-only patch rows;
3. fail closed on config load/reset failures;
4. avoid policy action, measured rollout, controller ranking, and paper claims.
```

## Next Branch Decision

Decision:

```text
continue
```

Next branch:

```text
paper_route_current_sim_dual_axis_candidate_pack_reset_validation
```

Next milestone:

```text
m2352-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-design
```

M2352 should design a bounded reset-validation protocol over the five M2350
config packs. It should not run reset validation yet. It should define:

```text
pack list;
scenario count expectations;
metadata-only caveat reporting;
reset pass/fail criteria;
output artifacts;
claim boundary;
follow-up implementation route.
```

## Blocked Routes

Blocked:

```text
direct controller comparison;
support-policy ranking;
driver checkpoint promotion;
training or PPO repair;
finite-window vs GRU comparison;
level3 self-ID claim;
paper-level current-sim result;
high-fidelity validation;
direct reset-validation execution without design;
direct patch-resolution repair before reset-validation design.
```

## Follow-Up Manifest

```text
experiments/manifests/m2352-paper-route-current-sim-dual-axis-candidate-pack-reset-validation-design.json
```
