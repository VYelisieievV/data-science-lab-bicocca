**Table 10 — Association covariance and first-difference robustness**

| outcome_key | outcome | estimator | coefficient | std_error | p_value | ci_low | ci_high | standardized_coefficient | n_obs | n_countries | fdr_q_value | reject_fdr_05 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| composite | Composite | cluster_country | -0.0638 | 0.0304 | 0.0358 | -0.1234 | -0.0042 | -0.0970 | 3940 | 95 | — | False |
| composite | Composite | cluster_country_year | -0.0638 | 0.0300 | 0.0336 | -0.1226 | -0.0049 | -0.0970 | 3940 | 95 | — | False |
| composite | Composite | driscoll_kraay | -0.0638 | 0.0141 | 0.0000 | -0.0914 | -0.0362 | -0.0970 | 3940 | 95 | — | False |
| composite | Composite | first_difference | -0.0208 | 0.0173 | 0.2289 | -0.0546 | 0.0131 | -0.0519 | 3845 | 95 | — | False |
| executive | Executive | cluster_country | 0.0165 | 0.0407 | 0.6847 | -0.0633 | 0.0964 | 0.0209 | 3940 | 95 | 0.6847 | False |
| executive | Executive | cluster_country_year | 0.0165 | 0.0401 | 0.6799 | -0.0621 | 0.0951 | 0.0209 | 3940 | 95 | 0.6799 | False |
| executive | Executive | driscoll_kraay | 0.0165 | 0.0150 | 0.2702 | -0.0129 | 0.0460 | 0.0209 | 3940 | 95 | 0.2702 | False |
| executive | Executive | first_difference | 0.0076 | 0.0218 | 0.7266 | -0.0351 | 0.0504 | 0.0141 | 3845 | 95 | 0.7266 | False |
| public_sector | Public sector | cluster_country | -0.0734 | 0.0385 | 0.0567 | -0.1489 | 0.0021 | -0.0971 | 3940 | 95 | 0.1134 | False |
| public_sector | Public sector | cluster_country_year | -0.0734 | 0.0379 | 0.0525 | -0.1476 | 0.0008 | -0.0971 | 3940 | 95 | 0.1051 | False |
| public_sector | Public sector | driscoll_kraay | -0.0734 | 0.0132 | 0.0000 | -0.0993 | -0.0476 | -0.0971 | 3940 | 95 | 0.0000 | True |
| public_sector | Public sector | first_difference | -0.0184 | 0.0182 | 0.3120 | -0.0541 | 0.0173 | -0.0383 | 3845 | 95 | 0.4160 | False |
| legislative | Legislative | cluster_country | -0.2431 | 0.1727 | 0.1594 | -0.5818 | 0.0956 | -0.0758 | 3745 | 95 | 0.2125 | False |
| legislative | Legislative | cluster_country_year | -0.2431 | 0.1698 | 0.1524 | -0.5761 | 0.0899 | -0.0758 | 3745 | 95 | 0.2032 | False |
| legislative | Legislative | driscoll_kraay | -0.2431 | 0.0646 | 0.0002 | -0.3698 | -0.1164 | -0.0758 | 3745 | 95 | 0.0002 | True |
| legislative | Legislative | first_difference | -0.1049 | 0.0750 | 0.1616 | -0.2519 | 0.0420 | -0.0507 | 3621 | 95 | 0.3232 | False |
| judicial | Judicial | cluster_country | -0.5395 | 0.1758 | 0.0022 | -0.8843 | -0.1948 | -0.1735 | 3940 | 95 | 0.0087 | True |
| judicial | Judicial | cluster_country_year | -0.5395 | 0.1751 | 0.0021 | -0.8828 | -0.1962 | -0.1735 | 3940 | 95 | 0.0083 | True |
| judicial | Judicial | driscoll_kraay | -0.5395 | 0.0799 | 0.0000 | -0.6961 | -0.3830 | -0.1735 | 3940 | 95 | 0.0000 | True |
| judicial | Judicial | first_difference | -0.1631 | 0.0767 | 0.0335 | -0.3134 | -0.0128 | -0.0802 | 3845 | 95 | 0.1339 | False |
