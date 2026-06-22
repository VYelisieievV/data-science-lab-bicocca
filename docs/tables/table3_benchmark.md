**Table 3 - Model benchmark (within-R2 vs OOF-R2; not directly comparable)**

| model | metric_type | r2 |
|---|---|---|
| Persistence baseline (corr ~ lag + country FE) | within-R² | 0.886 |
| TWFE M2 (populism + log GDP) | within-R² | -0.059 |
| Linear, GroupKFold | OOF-R² | 0.38 |
| XGBoost, GroupKFold | OOF-R² | 0.453 |
