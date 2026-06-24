# Decomposition tables

All files in this directory are generated from the committed processed panel by:

```bash
uv run --extra analysis python scripts/generate_decomposition_artifacts.py
```

Primary evidence:

- `table1_outcome_diagnostics`: coverage and identifying variation;
- `table2_twfe_m3`: controlled contemporaneous estimates;
- `table4_direction_joint_tests`: lead-lag and Granger-style joint tests;
- `table5_direction_lag_coefficients`: individual lag estimates;
- `table12_cross_dimension_summary`: compact synthesis.

Robustness evidence:

- `table3_twfe_stability`: M1–M3 stability;
- `table6_placebo_leads`: future-value falsification tests;
- `table7_first_differences`: lagged-change direction checks;
- `table8_democracy_interactions`: secondary heterogeneity;
- `table9_electoral_robustness`: election/forward-fill samples;
- `table10_association_robustness`: covariance and contemporaneous-change checks;
- `table11_measurement_robustness`: continuous versus five-level outcomes.

CSV files retain full numerical precision. Markdown versions are presentation copies rounded to four
decimal places. Blank FDR cells for the composite are intentional: it is a benchmark, not part of the
four-subtype discovery family.
