# Experiment Module

Sizing an experiment before it runs, and measuring it after.

```python
from otter.experiment import sample_size_for_mean, assign_groups, compare_groups

# How many units to detect a 2% lift on a metric averaging 120, sd 300?
size = sample_size_for_mean(baseline_mean=120, baseline_sd=300, min_lift_pct=2)
size.treatment_n, size.control_n, size.total_n

# Randomise reproducibly, then measure.
assign_groups(user_ids, {"control": 0.5, "treatment": 0.5}, seed=1)
compare_groups(data, group_col="group", metric_cols=["revenue", "orders"],
               control="control", treatment="treatment")
```

Comparisons use Welch's t-test (unequal variances are handled, not assumed away) with Benjamini-Hochberg correction across metrics. Two things worth knowing:

- The `cuped_pre=` reduces variance using a pre-period covariate, so the same sample detects a smaller effect. The covariate must be measured before assignment.
- `pretest_balance()` checks the randomisation actually worked. A pre-period that is empty (new units, no history) is reported as uninformative rather than tested, because a degenerate t-test returns a confident answer built on nothing.

`detectable_lift_for_mean()` and `detectable_lift_for_proportion()` run the other direction: the sample is fixed, so what can it actually see?
