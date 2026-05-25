# M831 V4 Low-Margin New Data Route Second Branch Synthesis

## Purpose

M831 synthesizes the second `v4_low_margin_new_data_route` window from M821
through M830 before any new implementation milestone.

This is a workflow synthesis milestone:

```text
no replay
no calibrator training
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

The synthesis decision is:

```text
continue
```

The branch should continue, but only into the no-training near-boundary
wrong-history pair-mining implementation designed by M830. PPO, actor updates,
residual-head updates, learned gating, and driver promotion remain blocked.

## Evidence Summary

### M821

M821 implemented the exact non-PPO fixed scalar/vector calibration grid admitted
by the first branch synthesis:

```text
candidate gates: 53
normal replay rows: 4505
intervention replay rows: 13515
train rows: 57
holdout rows: 28
```

The train-only selector picked identity. No nonidentity scalar/vector gate
improved p05 margin lift while preserving gates.

### M822

M822 audited M821 as a clean identity-only negative:

```text
identity ranked first
scalar 0.999 train p05 lift:  -1.07e-7
scalar 0.999 holdout p05 lift: -6.67e-7
actor and M761 residual-head checksums unchanged
```

This closed fixed scalar/vector residual suppression on the M814/M817 corpus.

### M823

M823 rejected same-corpus fixed-gate tuning and learned adaptive gate training
from an identity-only result. It selected a new evidence route: extreme
hidden-dynamics data mining for source-diverse command-response-history
necessity.

### M824

M824 designed the extreme hidden-dynamics data route. It preserved the
current-model/proxy-fault boundary:

```text
current_model_fault rows may support current model claims
current_model_proxy rows are stress proxies only
future_only rows may not be used as current evidence
```

It required normal/reset/zero/delayed/wrong-history diagnostics, source/fault
diversity, and unchanged actor/residual-head checksums.

### M825

M825 implemented and ran the no-training route:

```text
fault specs: 18
source groups: 64
normal replay rows: 512
history intervention rows: 3072
matched action-divergent proxy pairs: 256
accepted self-ID raw rows: 47
balanced accepted self-ID rows: 18
balanced mitigation rows: 12
```

The result was sparse/source-concentrated. The strongest signal was
zero-command observation, not full response-history necessity.

### M826

M826 audited M825 as a clean sparse result. The full normal pool was broad, but
accepted rows collapsed to:

```text
accepted rows: 18
seeds: 2
source groups: 3
fault pairs: 3
warm-up modes: natural_policy only
```

This rejected reading M825 as full self-ID proof and admitted real wrong-cross-
fault history intervention design.

### M827

M827 designed no-training wrong-cross-fault hidden injection:

```text
env = left current geometry
obs_t = left current observation
hidden_t = right recurrent hidden
rollout continues in left env
```

It required evidence separation between wrong-history and zero-command
ablation.

### M828

M828 implemented the intervention and reconstructed pairs cleanly:

```text
selected pairs: 108
reconstructed pairs: 108
wrong-history replay rows: 756
accepted primary wrong-history rows: 0
```

The hidden injection was directionally meaningful:

```text
wrong_history_closer_to_right_action: 108 / 108
max first-action L2: 0.006900976889874039
max margin gap: 0.00002602146853414311
```

but too weak for the selected pairs.

### M829

M829 audited M828 and found the decisive limiter: pair-boundary slack.

```text
normal margin min: 0.21766916668222658
normal margin median: 1.0287735657138812
normal margin <=0.05: 0 / 108
```

M829 classified the failure as scenario sampling, not implementation or
contract failure.

### M830

M830 designed boundary-first matched different-fault pair mining:

```text
1. bracket sources into near-boundary normal-history outcomes;
2. then match different-fault snapshots by visible ego/scene distance;
3. require action divergence before wrong-history replay;
4. keep wrong-history evidence separate from zero-command evidence;
5. enforce source/fault/warm-up/onset diversity gates.
```

It also identified the process blocker: M821-M830 are ten non-synthesis
milestones after M820, so implementation must wait for this synthesis.

## Supported Claims

The second branch window supports these claims:

1. Fixed scalar/vector residual suppression is not the missing control variable
   on the M814/M817 corpus.
2. Extreme hidden-dynamics source mining can generate a broad normal replay pool
   and matched action-divergent proxy pairs.
3. The M568 actor and M761 residual head can be evaluated across current-model
   and proxy-fault stress scenarios without mutating deployable inputs.
4. Wrong-cross-fault hidden injection is implemented and directionally affects
   the first action.
5. The main M828 failure was boundary slack, so near-boundary pair mining is a
   justified next no-training implementation.
6. Workflow synthesis is necessary before implementation because the branch has
   reached cadence.

## Falsified Claims

The branch falsifies or fails to support these working claims:

```text
Fixed scalar/vector residual gates can improve the M814/M817 corpus.
```

M821/M822 selected identity and found no nonidentity margin-lift candidate.

```text
M825 already provides source-diverse full response-history self-ID evidence.
```

M825/M826 found sparse accepted rows, concentrated in two seeds and only
natural-policy warm-up.

```text
Action-divergent matched pairs alone are sufficient for wrong-history proof.
```

M828/M829 showed that action-divergent pairs with wide normal margins produce
tiny margin gaps.

```text
The project is ready for PPO or checkpoint promotion from this route.
```

It is not. The current evidence supports only no-training near-boundary pair
mining.

## Failure Taxonomy Summary

### scenario_sampling_failure

M825 produced sparse/source-concentrated accepted rows. M828 selected matched
pairs that were action-divergent but far from terminal boundary. M830 directly
addresses this by requiring boundary-first matching.

### metric_artifact

M821's identity gate and M828's `108/108` closer-to-right-action result are both
useful diagnostics but not driver evidence. Neither proves performance
improvement or outcome-level self-identification.

### objective_overfit

Repeated fixed-corpus tuning would overfit M814/M817. M823 stopped that route.
M830 also warns that boundary rows from one geometry axis or one source group
must not count as proof.

### contract_violation

No completed milestone in this window violated the actor input contract.
Contract violation remains a pre-registered failure type because near-boundary
mining must keep fault labels and hidden parameters as source-selection/logging
metadata only.

## Public Gate Overfit Risk

The main overfit risk is active-set narrowing:

```text
M814 primary rows -> M817 calibration -> M821 identity grid
M825 sparse self-ID rows -> M828 matched pairs -> M830 boundary design
```

The next implementation must avoid turning one public pair set into a new
single-row gate. It should therefore require:

```text
train-free data generation
source/fault/warm-up/onset diversity
explicit rejected rows with reasons
wrong-history evidence separated from zero-command evidence
no promotion from a sparse positive diagnostic
```

Private holdout remains promotion-only and should not be used to tune this
implementation.

## Next Branch Decision

Decision:

```text
continue
```

The branch continues only into:

```text
m832-v4-near-boundary-wrong-history-pair-mining-implementation
```

The permitted claim scope for M832 is narrow:

```text
no-training data-route implementation and gate classification only
```

M832 may produce:

```text
source-diverse near-boundary wrong-history corpus;
sparse positive diagnostic;
clean scenario-sampling negative;
or contract/runtime failure classification.
```

M832 may not:

```text
train actor parameters;
train the M761 residual head;
train a calibrator;
run PPO;
promote a checkpoint;
claim true wheel-level fault fidelity from proxy rows;
use hidden fault labels as actor input.
```

## Decision

Decision:

```text
v4_low_margin_new_data_route_continue_to_near_boundary_wrong_history_pair_mining
```

Next:

```text
m832-v4-near-boundary-wrong-history-pair-mining-implementation
```
