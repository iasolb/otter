# Transforms Reference

`transforms.py` provides reusable functions so you don't have to write
lambdas inline every time.

### Single-column transforms (Series → Series)

For use with `normalize_and_attach`:

| Function | Description | Example |
|----------|-------------|---------|
| `mean_center` | `x - mean(x)` | `pond.normalize_and_attach("age", mean_center, "age_c")` |
| `z_score` | `(x - mean) / std` | `pond.normalize_and_attach("gpa", z_score, "gpa_z")` |
| `min_max_scale` | Scale to [0, 1] | `pond.normalize_and_attach("score", min_max_scale, "score_01")` |
| `log_transform` | `ln(x)` | `pond.normalize_and_attach("income", log_transform, "log_inc")` |
| `log1p_transform` | `ln(1 + x)`, safe for zeros | `pond.normalize_and_attach("tickets", log1p_transform, "log_tix")` |
| `square` | `x²` | `pond.normalize_and_attach("exp", square, "exp_sq")` |
| `rank_transform` | Replace with rank | `pond.normalize_and_attach("score", rank_transform, "score_rank")` |

### Factory transforms (return a callable)

| Function | Description | Example |
|----------|-------------|---------|
| `winsorize(lower, upper)` | Clip at quantiles | `pond.normalize_and_attach("income", winsorize(0.01, 0.99), "inc_wins")` |
| `demean_by_group(group_col)` | Subtract group means | `pond.normalize_and_attach("income", demean_by_group(pond.data["industry"]), "inc_dm")` |

### Multi-column transforms (DataFrame → Series)

For use with `calculate_and_attach`:

| Function | Description | Example |
|----------|-------------|---------|
| `interaction` | Product of first two columns | `pond.calculate_and_attach(["edu", "exp"], interaction, "edu_x_exp")` |
| `row_mean` | Row-wise average | `pond.calculate_and_attach(["m", "r", "s"], row_mean, "avg")` |
| `row_sum` | Row-wise sum | `pond.calculate_and_attach(["q1", "q2"], row_sum, "total")` |
| `safe_ratio(num, denom)` | Division, 0 → NaN | `pond.calculate_and_attach(["rev", "vis"], safe_ratio("rev", "vis"), "rpv")` |
