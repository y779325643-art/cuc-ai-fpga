# Offline PC 2.1 cluster analysis

This package implements the analysis mechanics in the `paper1-v2.3` amendment
and v2.2 base plan §12. It performs no generation, network, HDL, hidden or
physical evaluation. Its outputs always have `official=false`,
`claim_authorized=false`, and `model_calls=0`. Numerical decisions do not
grant research or publication authority.

## Inputs and identity

The registered `pc21-analysis-manifest-v1` plans every M0–M5 result slot before
outcomes are joined. Slot identity includes family, design cluster, optional
dependency group, semantic instance, replicate, method, endpoint, task hash and
suite hash. M0/M2/M3/M4 use `initial`; M1/M5 use `B4`. Each paired block must
plan all six methods. Task IDs cannot change family, cluster or bound bytes
between methods or replicates.
Identical task bytes cannot be relabelled as independent clusters, even across
families. Shared hashes within one cluster remain valid. This exact-duplicate
guard does not prove semantic independence of differently encoded near copies;
the source/obligation and development-exposure audit is still required.

`pc21-analysis-results-v1` wraps a `results` list, with a manifest hash binding.
Each row names one planned slot and repeats task/suite hashes. `value` is a
true integer 0/1 for `outcome_class=design_outcome`, or null for
`infrastructure_unscorable/not_applicable`. Successful rows need a sealed
candidate SHA256. The execution reducer must verify actual terminal and
evaluator artifacts before supplying these rows; the analyzer checks bindings
and consistency, not authenticity of arbitrary caller assertions.

Absent result rows are retained as unknown. Design failures remain 0.
Not-applicable records stay distinct from failure and infrastructure unknowns;
an inapplicable common primary endpoint prevents an eligible main decision.
H-stage inapplicability for Direct belongs in stage records and must not turn
the common primary endpoint into not-applicable.

Budget states are `compliant/exceeded/unverifiable`; integrity states are
`intact/violation/unverifiable`. Missing or failed qualifications do not rewrite
observed semantic values. They restrict eligible comparisons separately.

## Estimation and inference

Replicates are averaged within configuration, configuration weights are
normalized within design cluster, clusters are averaged within family, and the
three current LLM families receive equal weight. Extra configurations or
replicates do not increase an independent cluster's target weight.

The two primary contrasts are M5−M1@B4 (`system`) and M4−M3@initial (`build`).
Both contrasts share each stratified design-cluster bootstrap draw, retaining
their covariance. Studentization uses the variance of independent family
cluster means; the boundary-null statistic centers bootstrap draws at the
observed estimate, then compares with the explicit delta. Holm includes both
hypotheses even if one has no computable p-value. Reported two-sided 95%
intervals are marginal, not simultaneous multiplicity-adjusted intervals.

Too few clusters, sparse discordance, unavailable/zero standard error or too
many degenerate resamples produce a `degenerate` status and null p/interval.
The finite-resample p correction prevents a simulated p-value of zero. Missing
X is assigned 0 and missing Y 1 only in the primary conservative analysis
copy; opposite bounds and a complete-cluster sensitivity estimate accompany
the full denominator. Original null outcomes are preserved.

**Dependency limit:** a dependency group spanning more than one design cluster,
including across families, is rejected. A coordinated dependency-group
bootstrap has not been implemented; the package never silently treats those
clusters as independent.

Every policy field is explicit: deltas, planning target effects, alpha,
missingness fraction/difference limits, bootstrap sample count/seed, minimum
clusters/discordance and degenerate-resample tolerance. There is no frozen
scientific threshold implied by a default example. Planned effects must exceed
their null boundaries. The policy document has contract version
`pc21-analysis-policy-v1`; the report binds its content hash.
The current registered CLI policy fixes alpha at 0.05. The pure Python numeric
API accepts an explicit alpha for development checks; that does not authorize
changing the research plan's testing family or significance level.

## Commands

From the repository root, using this checkout's `agent/src`:

```powershell
$env:PYTHONPATH = (Resolve-Path agent/src).Path
python -B -m sr2fpga_agent.analysis validate --manifest MANIFEST.json --results RESULTS.json
python -B -m sr2fpga_agent.analysis analyze --manifest MANIFEST.json --results RESULTS.json --policy POLICY.json --output artifacts/analysis/fresh-report.json
python -B -m sr2fpga_agent.analysis simulate --policy POLICY.json --trials 20 --clusters-per-family 8 --effect-heterogeneity 0.02 --shared-pair-fraction 0.5 --output artifacts/analysis/fresh-synthetic-check.json
```

The CLI checks registered input contracts and refuses to overwrite output.
Choose output files below `artifacts/`. JSON duplicate keys and nonfinite
numbers are rejected. Input reads have a 64MB local bound.

`simulate` uses synthetic Bernoulli outcomes, common cluster baseline/effect
variation and configurable sharing between the two paired contrasts. It can
also omit records to exercise missingness, and `--boundary-null` simulates
the requested delta boundary rather than the planning alternative. Parameters
which would clip conditional probabilities are rejected. Degenerate or
ineligible trials remain in the trial denominator. This development check is
not a real-LLM power guarantee, a freeze, or proof of type-I error calibration;
validate the actual proposed design and nuisance ranges before formal use.

## Focused validation

```powershell
python -B -m pytest agent/tests/test_sr2fpga_cluster_analysis.py -q -p no:cacheprovider --basetemp=artifacts/paper1-ai/<fresh-analysis-tests>
```

Tests use hand-derived weighting/missingness examples, known Holm values,
input-counterexamples, fixed-seed boundary-null checks and synthetic data.
They do not read real held-out outcomes or run candidate models.
